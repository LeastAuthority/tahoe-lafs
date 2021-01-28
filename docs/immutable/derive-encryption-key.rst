Derive Encryption Key
=====================

* CHK uses AES128 for encryption.
* The encryption key is the 16 byte prefix of the hash of the entire cleartext.

  * The tag includes the chosen parameters and a convergence secret.
  * The convergence secret can be randomized per-cleartext or held stable per-client.

.. code:: python

   hash(
     "allmydata_immutable_content_to_key_with_added_secret_v1+6:SECRET,9:3,10,1024," ,
     < all cleartext > ,
   ) = "8dc140e6fe831481a2005ae152ffe32a..."


.. note::

   * CHK uses AES128 for encryption.
   * The encryption key is the 16 byte prefix of the hash of the entire cleartext.

     * The tag includes the chosen parameters and a convergence secret.
     * The convergence secret can be randomized per-cleartext or held stable per-client.
     * Convergence is useful for deduplication

       * If you try to upload the same file twice, the second upload is skipped and relies on data from the first upload.
       * Everyone who shares the same convergence secret gets this behavior.
       * Anyone who doesn't has to upload the file themselves.
       * Trade-off between privacy and efficiency
