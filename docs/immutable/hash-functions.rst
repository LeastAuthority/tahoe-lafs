Hash Functions
==============

* Tahoe uses cryptographic hash functions to allow readers to verify integrity of data

  * Hash function turns an arbitrary data (string) into a short, unpredictable digest (string):

    ================== ======
           Data        Digest [1]_
    ================== ======
    Hello, world!      ``315f5bdb76d078c43b8ac0064e4a``
    Xello, world!      ``f8c3bf62a9aa3e6fc1619c250e48``
    <many MB of data>  ``ec90cf64b3176dee2a91cb83e2d1``
    ================== ======

  * If the data changes, the digest changes.
  * Tahoe transmits a digest via high-integrity channel.
  * This allows data to be transmitted via low-integrity.
  * The receiver can check the received data against the digest.
  * If and only if the computed and received digests match, integrity has been preserved.

* Tahoe uses tagged hash functions throughout

  * A tagged hash function is a hash function.
  * It differs from a plain hash function by producing an output distinctive to a certain context.

    ===== ================== ======
     Tag         Data        Digest [1]_
    ===== ================== ======
    red   Hello, world!      ``2d9b7f4fec3fcd639d61a3c73dc0``
    blue  Hello, world!      ``41edc513765a86701feacd88cdc8``
    blue  Xello, world!      ``aff21150bce409446bc00917019c``
    ===== ================== ======

  * All hash functions should be tagged hash functions.
  * This prevents one part of the system (eg **red**) from producing a digest that can be used to attack another part of the system (eg **blue**).
  * Red and blue create and expect different digests even for the same input.

* Tahoe uses tagged sha256d for almost everything.

  * sha256d is sha256 twice.
  * sha256d ( data ) = sha256 ( sha256 ( data ) )
  * Unless otherwise specified assume a hash is a tagged sha256d with a context-unique tag.

.. [1] SHA256 produces 32 bytes of output.
       These strings are shortened to better fit on the screen.
