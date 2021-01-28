Merkle Trees
============

.. image:: docs/immutable/images/ciphertext-hash-tree/800px-Hash_Tree.svg.png
.. source https://en.wikipedia.org/wiki/Merkle_tree

.. note::

   * Tahoe also uses Merkle trees.
   * A Merkle tree is a group of hashes that are related to each other.
   * Start at the bottom
   * In this example, there are four pieces of data - L1 - L4
   * Each leaf of the tree is the hash of one of these pieces of data

     * Node 0-0 near the bottom left is the hash of L1
     * 0-1 is the hash of L2, and so on

   * Each non-leaf is the hash of the two child hashes

     * Node 0 is the hash of node 0-0 and node 0-1 combined
     * Node 1 is the hash of node 1-0 and node 1-1 combined
     * and so on

   * Each hash can confirm the integrity of some part of your data

     * Node 0-0 confirms the integrity of L1
     * Node 0 confirms the integrity of L1 *and* L2
     * The top hash confirms the integrity of all data.

   * Useful for operating on part of the data
   * For example, break a video stream into 1 minute pieces
   * Now you can seek to minute 31 and verify just the leaf hash covering that minute
