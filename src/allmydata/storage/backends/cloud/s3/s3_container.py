
from zope.interface import implementer

import attr

try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    from elementtree.ElementTree import ParseError

from allmydata.storage.backends.cloud.cloud_common import IContainer, \
     CommonContainerMixin, ContainerListMixin


def configure_s3_container(storedir, config):
    accesskeyid = config.get_config("storage", "s3.access_key_id")
    secretkey = config.get_or_create_private_config("s3secret")
    url = config.get_config("storage", "s3.url", "http://s3.amazonaws.com")
    container_name = config.get_config("storage", "s3.bucket")
    key_prefix = config.get_config("storage", "s3.prefix", "")

    return S3Container(accesskeyid, secretkey, url, container_name, key_prefix)



class _PrefixedKeys(object):
    """
    ``_PrefixedKeys`` is a minimal wrapper for the txAWS ``S3Client``
    interface.  It applies a prefix to all object keys that pass through it.
    This results in a transparent relocation of the objects from the top of
    the bucket to a particular prefix.

    For example, application code using this client may try to interact with
    an object at key ``foo``.  If the prefix is ``bar/`` then the actual AWS
    interaction will be with an object at key ``bar/foo``.
    """
    def __init__(self, client, key_prefix):
        self._client = client
        self._key_prefix = key_prefix


    def create(self, name):
        """
        Create the overall container.

        This is orthogonal to the object prefix.  There is no initialization
        required to begin using object keys with a particular prefix apart
        from creating the container.
        """
        return self._client.create(name)


    def delete(self, name):
        """
        Delete the overall container.

        This is orthogonal to the object prefix.  However, other prefixes may
        be in use by other agents.  The overall container should only be
        deleted when it is not in use by any agents.  This implementation of
        delete will fail if the container has any objects in it which will
        prevent any data-losing mis-uses of this API.
        """
        return self._client.delete(name)


    def get_bucket(self, *args, **kwargs):
        """
        Retrieve the contents of this container which have the appropriate prefix.

        The consumer of this API also wants to be able to specify a prefix.
        If both prefixes are present, combine them in the correct order to
        produce the overall desired result (the prefix at this level takes
        precedence; the prefix supply by the consumer of this API provides
        another level of hierarchy inferior to the first).

        The consumer of this API also wants to be able to specify a marker.
        Combine the prefix with the marker to create the correct marker value
        with respect to the prefixed region this object grants access to.
        """
        kwargs['prefix'] = self._key_prefix + kwargs.get('prefix', '')
        if 'marker' in kwargs:
            kwargs['marker'] = self._key_prefix + kwargs['marker']

        d = self._client.get_bucket(*args, **kwargs)
        def fix_prefixes(bucket):
            marker = None
            if bucket.marker is not None:
                marker = bucket.marker[len(self._key_prefix):]
            return attr.evolve(
                bucket,
                # Strip off the part of the prefix we're transparently
                # managing.
                prefix=bucket.prefix[len(self._key_prefix):],
                # And here.
                marker=marker,
                contents=list(
                    attr.evolve(
                        item,
                        # And here.
                        key=item.key[len(self._key_prefix):],
                    )
                    for item
                    in bucket.contents
                ),
            )
        d.addCallback(fix_prefixes)
        return d


    def _object_name(self, name):
        """
        Construct the name of an object including the prefix.
        """
        return self._key_prefix + name


    def put_object(self, bucket, name, *a):
        """
        Put data for an object.

        :param name: The unprefixed object name.  The prefix will be applied
            to determine the real object to which the data belongs.
        """
        return self._client.put_object(bucket, self._object_name(name), *a)


    def get_object(self, bucket, name):
        """
        Get data for an object.

        :param name: The unprefixed object name.  The prefix will be applied
            to determine the real object the data of which to get.
        """
        return self._client.get_object(bucket, self._object_name(name))



@implementer(IContainer)
class S3Container(ContainerListMixin, CommonContainerMixin):
    """
    I represent a real S3 container (bucket), accessed using the txaws library.
    """

    def __init__(self, access_key, secret_key, url, container_name, key_prefix, override_reactor=None):
        # We only depend on txaws when this class is actually instantiated.
        from txaws.credentials import AWSCredentials
        from txaws.service import AWSServiceEndpoint
        from txaws.s3.client import S3Client

        creds = AWSCredentials(access_key=access_key, secret_key=secret_key)
        endpoint = AWSServiceEndpoint(uri=url)
        self._init(
            S3Client(creds=creds, endpoint=endpoint),
            container_name,
            key_prefix,
            override_reactor,
        )

    def _init(self, s3_client, container_name, key_prefix, override_reactor):
        CommonContainerMixin.__init__(self, container_name, override_reactor)
        self.client = _PrefixedKeys(s3_client, key_prefix)

        from txaws.s3.exception import S3Error
        self.ServiceError = S3Error

    @classmethod
    def from_s3_client(cls, client, container_name, key_prefix, override_reactor=None):
        self = cls("x", "x", "", "", "")
        self._init(client, container_name, key_prefix, override_reactor)
        return self

    def _create(self):
        return self.client.create(self._container_name)

    def _delete(self):
        return self.client.delete(self._container_name)

    def list_some_objects(self, **kwargs):
        return self._do_request('list objects', self._list_some_objects, **kwargs)

    def _list_some_objects(self, **kwargs):
        d = self.client.get_bucket(self._container_name, **kwargs)
        def _err(f):
            f.trap(ParseError)
            raise self.ServiceError("", 500, "list objects: response body is not valid XML (possibly empty)\n" + f)
        d.addErrback(_err)
        return d

    def _put_object(self, object_name, data, content_type='application/octet-stream', metadata={}):
        return self.client.put_object(self._container_name, object_name, data, content_type, metadata)

    def _get_object(self, object_name):
        return self.client.get_object(self._container_name, object_name)

    def _head_object(self, object_name):
        return self.client.head_object(self._container_name, object_name)

    def _delete_object(self, object_name):
        return self.client.delete_object(self._container_name, object_name)

    def put_policy(self, policy):
        """
        Set access control policy on a bucket.
        """
        query = self.client.query_factory(
            action='PUT', creds=self.client.creds, endpoint=self.client.endpoint,
            bucket=self._container_name, object_name='?policy', data=policy)
        return self._do_request('PUT policy', query.submit)

    def get_policy(self):
        query = self.client.query_factory(
            action='GET', creds=self.client.creds, endpoint=self.client.endpoint,
            bucket=self._container_name, object_name='?policy')
        return self._do_request('GET policy', query.submit)

    def delete_policy(self):
        query = self.client.query_factory(
            action='DELETE', creds=self.client.creds, endpoint=self.client.endpoint,
            bucket=self._container_name, object_name='?policy')
        return self._do_request('DELETE policy', query.submit)
