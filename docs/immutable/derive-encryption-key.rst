Derive Encryption Key
=====================

* CHK uses AES128 for encryption.
* The encryption key is the 16 byte prefix of the hash of the entire cleartext.
  * The tag includes the chosen parameters and a convergence secret.
  * The convergence secret can be randomized per-cleartext or held stable per-client. [1]_

.. [1] https://en.wikipedia.org/wiki/Convergent_encryption
