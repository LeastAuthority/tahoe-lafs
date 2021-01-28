Forward Erasure Encode
======================

* Use **required** and **total** to FEC-encode each segment separately.
* Each segment encodes to a list blocks (number of **blocks** equals **total**).
* FEC requires an input to have length that is multiple of **required**

  * Pad the last segment with NUL if necessary

* Ultimately the first block for all segments will be put in the first share,
  the second block for all segments will be put in the second share,
  etc.

.. image:: docs/immutable/images/encode/fec.png


.. note::

   * Use **required** and **total** to FEC-encode each segment separately.
   * Each segment encodes to a list blocks (number of **blocks** equals **total**).
   * FEC requires an input to have length that is multiple of **required**

     * Pad the last segment with NUL if necessary

   * Ultimately the first block for all segments will be put in the first share,
     the second block for all segments will be put in the second share,
     and so on.
