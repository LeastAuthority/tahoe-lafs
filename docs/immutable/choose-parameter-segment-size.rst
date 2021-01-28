Choose Parameters - Segment Size
================================

The hashing scheme involves splitting large files into *segments* - smaller pieces of mostly-fixed size.

  .. image:: docs/immutable/images/choose-parameters/segments.png

Nothing is segmented yet.
We just choose the parameter.


.. note::

   * The hashing scheme involves splitting large files into *segments* -
     These are just smaller pieces of a chosen size.
   * This is not exposed in Tahoe UI
   * Therefore in practice this is always 128 kB
   * This determines how much data goes into each leaf of some merkle trees we will construct
