"""
HTTP client that talks to the HTTP storage server.
"""

from typing import Union, Set, Optional

from base64 import b64encode

import attr

# TODO Make sure to import Python version?
from cbor2 import loads, dumps
from collections_extended import RangeMap
from werkzeug.datastructures import Range, ContentRange
from twisted.web.http_headers import Headers
from twisted.web import http
from twisted.web.iweb import IPolicyForHTTPS
from twisted.internet.defer import inlineCallbacks, returnValue, fail, Deferred
from twisted.internet.interfaces import IOpenSSLClientConnectionCreator
from twisted.internet.ssl import CertificateOptions
from twisted.web.client import Agent, HTTPConnectionPool
from zope.interface import implementer
from hyperlink import DecodedURL
import treq
from treq.client import HTTPClient
from treq.testing import StubTreq
from OpenSSL import SSL
from cryptography.hazmat.bindings.openssl.binding import Binding

from .http_common import (
    swissnum_auth_header,
    Secrets,
    get_content_type,
    CBOR_MIME_TYPE,
    get_spki_hash,
)
from .common import si_b2a
from ..util.hashutil import timing_safe_compare

_OPENSSL = Binding().lib


def _encode_si(si):  # type: (bytes) -> str
    """Encode the storage index into Unicode string."""
    return str(si_b2a(si), "ascii")


class ClientException(Exception):
    """An unexpected response code from the server."""

    def __init__(self, code, *additional_args):
        Exception.__init__(self, code, *additional_args)
        self.code = code


def _decode_cbor(response):
    """Given HTTP response, return decoded CBOR body."""
    if response.code > 199 and response.code < 300:
        content_type = get_content_type(response.headers)
        if content_type == CBOR_MIME_TYPE:
            # TODO limit memory usage
            # https://tahoe-lafs.org/trac/tahoe-lafs/ticket/3872
            return treq.content(response).addCallback(loads)
        else:
            raise ClientException(-1, "Server didn't send CBOR")
    else:
        return fail(ClientException(response.code, response.phrase))


@attr.s
class ImmutableCreateResult(object):
    """Result of creating a storage index for an immutable."""

    already_have = attr.ib(type=Set[int])
    allocated = attr.ib(type=Set[int])


class _TLSContextFactory(CertificateOptions):
    """
    Create a context that validates the way Tahoe-LAFS wants to: based on a
    pinned certificate hash, rather than a certificate authority.

    Originally implemented as part of Foolscap.
    """

    def __init__(self, expected_spki_hash: bytes):
        self.expected_spki_hash = expected_spki_hash
        CertificateOptions.__init__(self)

    def getContext(self) -> SSL.Context:
        def always_validate(conn, cert, errno, depth, preverify_ok):
            # This function is called to validate the certificate received by
            # the other end. OpenSSL calls it multiple times, for each errno
            # for each certificate.

            # We do not care about certificate authorities or revocation
            # lists, we just want to know that the certificate has a valid
            # signature and follow the chain back to one which is
            # self-signed. We need to protect against forged signatures, but
            # not the usual TLS concerns about invalid CAs or revoked
            # certificates.
            things_are_ok = (
                _OPENSSL.X509_V_OK,
                _OPENSSL.X509_V_ERR_CERT_NOT_YET_VALID,
                _OPENSSL.X509_V_ERR_CERT_HAS_EXPIRED,
                _OPENSSL.X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT,
                _OPENSSL.X509_V_ERR_SELF_SIGNED_CERT_IN_CHAIN,
            )
            # TODO can we do this once instead of multiple times?
            if errno in things_are_ok and timing_safe_compare(
                get_spki_hash(cert.to_cryptography()), self.expected_spki_hash
            ):
                return 1
            # TODO: log the details of the error, because otherwise they get
            # lost in the PyOpenSSL exception that will eventually be raised
            # (possibly OpenSSL.SSL.Error: certificate verify failed)
            return 0

        ctx = CertificateOptions.getContext(self)

        # VERIFY_PEER means we ask the the other end for their certificate.
        ctx.set_verify(SSL.VERIFY_PEER, always_validate)
        return ctx


@implementer(IPolicyForHTTPS)
@implementer(IOpenSSLClientConnectionCreator)
@attr.s
class _StorageClientHTTPSPolicy:
    """
    A HTTPS policy that ensures the SPKI hash of the public key matches a known
    hash, i.e. pinning-based validation.
    """

    expected_spki_hash = attr.ib(type=bytes)

    # IPolicyForHTTPS
    def creatorForNetloc(self, hostname, port):
        return self

    # IOpenSSLClientConnectionCreator
    def clientConnectionForTLS(self, tlsProtocol):
        return SSL.Connection(
            _TLSContextFactory(self.expected_spki_hash).getContext(), None
        )


class StorageClient(object):
    """
    Low-level HTTP client that talks to the HTTP storage server.
    """

    def __init__(
        self, url, swissnum, treq=treq
    ):  # type: (DecodedURL, bytes, Union[treq,StubTreq,HTTPClient]) -> None
        """
        The URL is a HTTPS URL ("https://...").  To construct from a NURL, use
        ``StorageClient.from_nurl()``.
        """
        self._base_url = url
        self._swissnum = swissnum
        self._treq = treq

    @classmethod
    def from_nurl(cls, nurl: DecodedURL, reactor, persistent: bool = True) -> "StorageClient":
        """
        Create a ``StorageClient`` for the given NURL.

        ``persistent`` indicates whether to use persistent HTTP connections.
        """
        assert nurl.fragment == "v=1"
        assert nurl.scheme == "pb"
        swissnum = nurl.path[0].encode("ascii")
        certificate_hash = nurl.user.encode("ascii")

        treq_client = HTTPClient(
            Agent(
                reactor,
                _StorageClientHTTPSPolicy(expected_spki_hash=certificate_hash),
                pool=HTTPConnectionPool(reactor, persistent=persistent),
            )
        )

        https_url = DecodedURL().replace(scheme="https", host=nurl.host, port=nurl.port)
        return cls(https_url, swissnum, treq_client)

    def relative_url(self, path):
        """Get a URL relative to the base URL."""
        return self._base_url.click(path)

    def _get_headers(self, headers):  # type: (Optional[Headers]) -> Headers
        """Return the basic headers to be used by default."""
        if headers is None:
            headers = Headers()
        headers.addRawHeader(
            "Authorization",
            swissnum_auth_header(self._swissnum),
        )
        return headers

    def request(
        self,
        method,
        url,
        lease_renew_secret=None,
        lease_cancel_secret=None,
        upload_secret=None,
        headers=None,
        message_to_serialize=None,
        **kwargs
    ):
        """
        Like ``treq.request()``, but with optional secrets that get translated
        into corresponding HTTP headers.

        If ``message_to_serialize`` is set, it will be serialized (by default
        with CBOR) and set as the request body.
        """
        headers = self._get_headers(headers)

        # Add secrets:
        for secret, value in [
            (Secrets.LEASE_RENEW, lease_renew_secret),
            (Secrets.LEASE_CANCEL, lease_cancel_secret),
            (Secrets.UPLOAD, upload_secret),
        ]:
            if value is None:
                continue
            headers.addRawHeader(
                "X-Tahoe-Authorization",
                b"%s %s" % (secret.value.encode("ascii"), b64encode(value).strip()),
            )

        # Note we can accept CBOR:
        headers.addRawHeader("Accept", CBOR_MIME_TYPE)

        # If there's a request message, serialize it and set the Content-Type
        # header:
        if message_to_serialize is not None:
            if "data" in kwargs:
                raise TypeError(
                    "Can't use both `message_to_serialize` and `data` "
                    "as keyword arguments at the same time"
                )
            kwargs["data"] = dumps(message_to_serialize)
            headers.addRawHeader("Content-Type", CBOR_MIME_TYPE)

        return self._treq.request(method, url, headers=headers, **kwargs)


class StorageClientGeneral(object):
    """
    High-level HTTP APIs that aren't immutable- or mutable-specific.
    """

    def __init__(self, client):  # type: (StorageClient) -> None
        self._client = client

    @inlineCallbacks
    def get_version(self):
        """
        Return the version metadata for the server.
        """
        url = self._client.relative_url("/v1/version")
        response = yield self._client.request("GET", url)
        decoded_response = yield _decode_cbor(response)
        returnValue(decoded_response)


@attr.s
class UploadProgress(object):
    """
    Progress of immutable upload, per the server.
    """

    # True when upload has finished.
    finished = attr.ib(type=bool)
    # Remaining ranges to upload.
    required = attr.ib(type=RangeMap)


class StorageClientImmutables(object):
    """
    APIs for interacting with immutables.
    """

    def __init__(self, client: StorageClient):
        self._client = client

    @inlineCallbacks
    def create(
        self,
        storage_index,
        share_numbers,
        allocated_size,
        upload_secret,
        lease_renew_secret,
        lease_cancel_secret,
    ):  # type: (bytes, Set[int], int, bytes, bytes, bytes) -> Deferred[ImmutableCreateResult]
        """
        Create a new storage index for an immutable.

        TODO https://tahoe-lafs.org/trac/tahoe-lafs/ticket/3857 retry
        internally on failure, to ensure the operation fully succeeded.  If
        sufficient number of failures occurred, the result may fire with an
        error, but there's no expectation that user code needs to have a
        recovery codepath; it will most likely just report an error to the
        user.

        Result fires when creating the storage index succeeded, if creating the
        storage index failed the result will fire with an exception.
        """
        url = self._client.relative_url("/v1/immutable/" + _encode_si(storage_index))
        message = {"share-numbers": share_numbers, "allocated-size": allocated_size}

        response = yield self._client.request(
            "POST",
            url,
            lease_renew_secret=lease_renew_secret,
            lease_cancel_secret=lease_cancel_secret,
            upload_secret=upload_secret,
            message_to_serialize=message,
        )
        decoded_response = yield _decode_cbor(response)
        returnValue(
            ImmutableCreateResult(
                already_have=decoded_response["already-have"],
                allocated=decoded_response["allocated"],
            )
        )

    @inlineCallbacks
    def abort_upload(
        self, storage_index: bytes, share_number: int, upload_secret: bytes
    ) -> Deferred[None]:
        """Abort the upload."""
        url = self._client.relative_url(
            "/v1/immutable/{}/{}/abort".format(_encode_si(storage_index), share_number)
        )
        response = yield self._client.request(
            "PUT",
            url,
            upload_secret=upload_secret,
        )

        if response.code == http.OK:
            return
        else:
            raise ClientException(
                response.code,
            )

    @inlineCallbacks
    def write_share_chunk(
        self, storage_index, share_number, upload_secret, offset, data
    ):  # type: (bytes, int, bytes, int, bytes) -> Deferred[UploadProgress]
        """
        Upload a chunk of data for a specific share.

        TODO https://tahoe-lafs.org/trac/tahoe-lafs/ticket/3857 The
        implementation should retry failed uploads transparently a number of
        times, so that if a failure percolates up, the caller can assume the
        failure isn't a short-term blip.

        Result fires when the upload succeeded, with a boolean indicating
        whether the _complete_ share (i.e. all chunks, not just this one) has
        been uploaded.
        """
        url = self._client.relative_url(
            "/v1/immutable/{}/{}".format(_encode_si(storage_index), share_number)
        )
        response = yield self._client.request(
            "PATCH",
            url,
            upload_secret=upload_secret,
            data=data,
            headers=Headers(
                {
                    "content-range": [
                        ContentRange("bytes", offset, offset + len(data)).to_header()
                    ]
                }
            ),
        )

        if response.code == http.OK:
            # Upload is still unfinished.
            finished = False
        elif response.code == http.CREATED:
            # Upload is done!
            finished = True
        else:
            raise ClientException(
                response.code,
            )
        body = yield _decode_cbor(response)
        remaining = RangeMap()
        for chunk in body["required"]:
            remaining.set(True, chunk["begin"], chunk["end"])
        returnValue(UploadProgress(finished=finished, required=remaining))

    @inlineCallbacks
    def read_share_chunk(
        self, storage_index, share_number, offset, length
    ):  # type: (bytes, int, int, int) -> Deferred[bytes]
        """
        Download a chunk of data from a share.

        TODO https://tahoe-lafs.org/trac/tahoe-lafs/ticket/3857 Failed
        downloads should be transparently retried and redownloaded by the
        implementation a few times so that if a failure percolates up, the
        caller can assume the failure isn't a short-term blip.

        NOTE: the underlying HTTP protocol is much more flexible than this API,
        so a future refactor may expand this in order to simplify the calling
        code and perhaps download data more efficiently.  But then again maybe
        the HTTP protocol will be simplified, see
        https://tahoe-lafs.org/trac/tahoe-lafs/ticket/3777
        """
        url = self._client.relative_url(
            "/v1/immutable/{}/{}".format(_encode_si(storage_index), share_number)
        )
        response = yield self._client.request(
            "GET",
            url,
            headers=Headers(
                {"range": [Range("bytes", [(offset, offset + length)]).to_header()]}
            ),
        )
        if response.code == http.PARTIAL_CONTENT:
            body = yield response.content()
            returnValue(body)
        else:
            raise ClientException(response.code)

    @inlineCallbacks
    def list_shares(self, storage_index):  # type: (bytes,) -> Deferred[Set[int]]
        """
        Return the set of shares for a given storage index.
        """
        url = self._client.relative_url(
            "/v1/immutable/{}/shares".format(_encode_si(storage_index))
        )
        response = yield self._client.request(
            "GET",
            url,
        )
        if response.code == http.OK:
            body = yield _decode_cbor(response)
            returnValue(set(body))
        else:
            raise ClientException(response.code)

    @inlineCallbacks
    def add_or_renew_lease(
        self, storage_index: bytes, renew_secret: bytes, cancel_secret: bytes
    ):
        """
        Add or renew a lease.

        If the renewal secret matches an existing lease, it is renewed.
        Otherwise a new lease is added.
        """
        url = self._client.relative_url(
            "/v1/lease/{}".format(_encode_si(storage_index))
        )
        response = yield self._client.request(
            "PUT",
            url,
            lease_renew_secret=renew_secret,
            lease_cancel_secret=cancel_secret,
        )

        if response.code == http.NO_CONTENT:
            return
        else:
            raise ClientException(response.code)

    @inlineCallbacks
    def advise_corrupt_share(
        self,
        storage_index: bytes,
        share_number: int,
        reason: str,
    ):
        """Indicate a share has been corrupted, with a human-readable message."""
        assert isinstance(reason, str)
        url = self._client.relative_url(
            "/v1/immutable/{}/{}/corrupt".format(
                _encode_si(storage_index), share_number
            )
        )
        message = {"reason": reason}
        response = yield self._client.request("POST", url, message_to_serialize=message)
        if response.code == http.OK:
            return
        else:
            raise ClientException(
                response.code,
            )
