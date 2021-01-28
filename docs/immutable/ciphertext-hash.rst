Ciphertext Hash
===============

* Hash the whole ciphertext to get the "ciphertext hash".
* A reader can use this later as the simplest way to verify **integrity** of the data.
* The downside of the simplicity is that only integrity the *complete* data can be verified

  * You can't download the first half and check that.

.. image:: docs/immutable/images/ciphertext-hash/ciphertext-hash.png

.. note::

   * Hash the whole ciphertext to get the "ciphertext hash".
   * A reader can use this later as the simplest way to verify integrity of the data.
   * The downside of the simplicity is that only integrity the *complete* data can be verified

     * For example, you can't download the first half and check that.
