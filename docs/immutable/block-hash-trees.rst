Block Hash Trees
================

* For each share,
  take all of the blocks that belong to that share
  and use them as the leaves of a merkle tree.
* The result is one merkle tree for each share.
* One of these trees protects all of the blocks in one share.

.. image:: docs/immutable/images/block-hash-trees/block-hash-tree.png

.. note::

   * For each share,
     take all of the blocks that belong to that share
     and use them as the leaves of a merkle tree.
   * The result is one merkle tree for each share.
   * One of these trees protects all of the blocks in one share.
