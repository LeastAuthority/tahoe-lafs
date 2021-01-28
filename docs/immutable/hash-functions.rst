Hash Functions
==============

* Hash functions help provide data **integrity**
* A hash function accepts arbitrary data (string) as input
* It produces a short digest (string) as output

  * One-way
  * Collision-resistant

  .. code:: python

     hash( "Hello, world!" ) = "315f5bdb76d078c43b8ac0064e4a"
     hash( "Xello, world!" ) = "f8c3bf62a9aa3e6fc1619c250e48"
     hash( <many MB>       ) = "ec90cf64b3176dee2a91cb83e2d1"

.. note::

   * First some introductions
   * What is a hash function?
   * Hash functions help provide data **integrity**
   * A hash function accepts arbitrary data (string) as input
   * It produces a short digest (string) as output
   * One-way: Given the digest you cannot recover the input
   * Collision-resistant: It minimizes the chance that two different inputs have the same digest
   * In Tahoe, when you store data you also hash it.
   * You remember (locally store) the digest.
   * When you download the data, you re-compute the digest.
   * If and only if the computed and received digests match, integrity has been preserved.
