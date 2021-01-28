Encrypt
=======

* This is the exciting part right?
* Encrypt the cleartext using AES128 in CTR-mode using the derived key.

  .. image:: docs/immutable/images/encrypt/encrypt.png

* Now you have the ciphertext.
* That was exciting right?


.. note::

   * Tahoe always uses a nonce of all NULs
   * It uses an increment-by-one counter function
   * If you ever encrypt different data with the same AES128 key and nonce, you lose
   * As just mentioned, Tahoe derives the key from the content so it only ever use a key with one dataset
   * At this point we have confidentiality.
   * This is really one of the most standard pieces of the scheme.
