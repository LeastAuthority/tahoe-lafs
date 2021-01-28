SHA256d
=======

* Tahoe uses tagged sha256d for almost everything.
* sha256d is "double" sha256.
* Unless otherwise specified assume a hash is a tagged sha256d with a context-unique tag.

  .. code:: python

     sha256d ( data ) = sha256 ( sha256 ( data ) )
     tagged_sha256d( "red", "Hello, world!" )
       = "deeebd2d5bf65f68b144453915266c34ccb2f5d322953639b4b600eddd40949d"

.. note::

   * Tahoe uses tagged sha256d for almost everything.
   * sha256d is double sha256 - that is, sha256 twice.
   * As you can see the digest looks just like a sha256 digest
   * Unless otherwise specified assume a hash is a tagged sha256d with a context-unique tag.
