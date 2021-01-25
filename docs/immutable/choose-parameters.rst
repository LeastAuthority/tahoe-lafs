Choose Parameters
====================

* The encryption scheme (for confidentiality) involves splitting large files into *segments*
  (smaller pieces of mostly-fixed size).
* The maximum segment size is a parameter.
* But it's not exposed in the UI so it's always 128kB.
* The encoding scheme (for availability) involves splitting the segments into blocks and adding some redundancy.
  * The **total** number of blocks is a parameter.
    The default value is 10.
    This is also sometimes called ``n``.
  * The **required** number of blocks is also a parameter.
    The default value is 3.
    This is also sometimes called ``k``.
