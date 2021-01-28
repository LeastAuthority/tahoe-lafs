Ciphertext Hash Tree 2/2
========================

Construct a Merkle tree with hashes as its leaves.

.. image:: docs/immutable/images/ciphertext-hash-tree/ciphertext-hash-tree.png


.. note::

   * Because of the properties of Merkle trees,
     hashes in this tree allow integrity verification of different amounts of the ciphertext.
   * eg, video use-case mentioned earlier is now possible

     * Download and verify only the ciphertext you need
       (rounded up to nearest segment)
