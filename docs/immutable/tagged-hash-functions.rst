Tagged Hash Functions
=====================

* Tahoe uses tagged hash functions throughout
* A tagged hash function is a hash function.
* Beyond plain hash functions, it will an output distinctive to a certain context.


  .. code:: python

     tagged_hash( "red" , "Hello, world!" ) = "2d9b7f4fec3fcd639d61a3c73dc0"
     tagged_hash( "blue", "Hello, world!" ) = "41edc513765a86701feacd88cdc8"
     tagged_hash( "blue", "Xello, world!" ) = "aff21150bce409446bc00917019c"

.. note::

   * Next - Tagged hash functions
   * A tagged hash function is a hash function.
   * Beyond plain hash functions, it produces an output distinctive to a certain context.
   * This prevents one part of the system (in this example **red**) from producing a digest that can be used to attack another part of the system (in this example **blue**).
   * Red and blue create and expect different digests even for the same input.
