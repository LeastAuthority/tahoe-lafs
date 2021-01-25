Forward Erasure Encode
======================

* Use **required** and **total** to FEC-encode each segment separately.
* Each segment encodes to a list of **total** blocks.
* FEC requires an input to have length that is multiple of **required**

  * Pad the last segment with NUL if necessary
