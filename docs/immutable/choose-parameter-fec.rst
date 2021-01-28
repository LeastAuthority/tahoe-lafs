Choose Parameters - Required and Total
======================================

* The encoding scheme supports improved **availability** by choosing values for two more parameters.
* The **total** (aka **n**) number of blocks is a parameter.
  The default value is 10.
* The **required** (aka **k**) number of blocks is also a parameter.
  The default value is 3.

.. note::

   * Next we choose parameters that control availability.
   * Availability comes from always being able to download enough data to reconstruct the input.
   * Tahoe makes this more likely by adding redundancy to the data so you store more than you need to recover the input.
   * If some of the encoded data goes missing or is tampered with, you can find other intact data to replace it.
   * The parameters chosen here are:

     * "Total" - the total number of encoded pieces that are required to reconstruct the input.
     * "Required" - The minimum number of encoded pieces that are required to reconstruct the input.

   * So, for example,
     you can choose 10 total and 3 required and up to 7 pieces can get lost/damaged without the input being lost.
