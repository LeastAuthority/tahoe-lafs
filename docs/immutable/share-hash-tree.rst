Share Hash Tree
===============

Construct a Merkle tree with the root of each Block Hash Tree as leaves.

.. image:: docs/immutable/images/share-hash-tree/share-hash-tree.png
   :height: 525

.. note::

   * This step ties all of the block hash trees together in one "share hash tree".
   * In this example, the top hash of each of the 10 block hash trees becomes
     a leaf in a new merkle tree.
   * The top hash of the share hash tree protects all of the blocks.
