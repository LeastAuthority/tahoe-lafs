:title: Tahoe-LAFS CHK (Immutables) Encryption & Encoding
:data-transition-duration: 150
:css: extra.css

CHK Encryption & Encoding
=========================

How Tahoe Handles Immutable Files
---------------------------------

.. note::

   * Hello and thanks for joining
   * Today I'm talking about Tahoe
   * Tahoe is a distributed, end-to-end-encrypted, high-availability storage system
   * LeastAuthority operates S4 based on Tahoe
   * PrivateStorage is also based on Tahoe
   * Tahoe lets you store your data on someone else's computer (eg in the cloud)
   * But it doesn't let anyone in the cloud read it or tamper with it
   * And it doesn't let the cloud prevent you from reading it (mostly)
   * Today I'm specifically talking about Tahoe's support for *immutable* files or "CHK capabilities"

     * these files are write-once
     * you upload them once and they can never be changed

  * More specifically, I'm going to go through the encryption and encoding of these files

----

Hash Functions
==============

* Hash functions help provide data **integrity**
* A hash function accepts arbitrary data (string) as input
* It produces a short digest (string) as output

  * One-way
  * Collision-resistant

  .. code:: python

     hash( "Hello, world!" ) = "315f5bdb76d078c43b8ac0064e4a"
     hash( "Xello, world!" ) = "f8c3bf62a9aa3e6fc1619c250e48"
     hash( <many MB>       ) = "ec90cf64b3176dee2a91cb83e2d1"

.. note::

   * First some introductions
   * What is a hash function?
   * Hash functions help provide data **integrity**
   * A hash function accepts arbitrary data (string) as input
   * It produces a short digest (string) as output
   * One-way: Given the digest you cannot recover the input
   * Collision-resistant: It minimizes the chance that two different inputs have the same digest
   * In Tahoe, when you store data you also hash it.
   * You remember (locally store) the digest.
   * When you download the data, you re-compute the digest.
   * If and only if the computed and received digests match, integrity has been preserved.

----

Tagged Hash Functions
=====================

* Tahoe uses tagged hash functions throughout
* A tagged hash function is a hash function.
* Beyond plain hash functions, it will an output distinctive to a certain context.


  .. code:: python

     tagged_hash( "red" , "Hello, world!" ) = "2d9b7f4fec3fcd639d61a3c73dc0"
     tagged_hash( "blue", "Hello, world!" ) = "41edc513765a86701feacd88cdc8"
     tagged_hash( "blue", "Xello, world!" ) = "aff21150bce409446bc00917019c"

.. note::

   * Next - Tagged hash functions
   * A tagged hash function is a hash function.
   * Beyond plain hash functions, it produces an output distinctive to a certain context.
   * This prevents one part of the system (in this example **red**) from producing a digest that can be used to attack another part of the system (in this example **blue**).
   * Red and blue create and expect different digests even for the same input.

----

SHA256d
=======

* Tahoe uses tagged sha256d for almost everything.
* sha256d is "double" sha256.
* Unless otherwise specified assume a hash is a tagged sha256d with a context-unique tag.

  .. code:: python

     sha256d ( data ) = sha256 ( sha256 ( data ) )
     tagged_sha256d( "red", "Hello, world!" )
       = "deeebd2d5bf65f68b144453915266c34ccb2f5d322953639b4b600eddd40949d"

.. note::

   * Tahoe uses tagged sha256d for almost everything.
   * sha256d is double sha256 - that is, sha256 twice.
   * As you can see the digest looks just like a sha256 digest
   * Unless otherwise specified assume a hash is a tagged sha256d with a context-unique tag.

----

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

----

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

----

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

----

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

----

Encrypt
=======

* This is the exciting part right?
* Encrypt the cleartext using AES128 in CTR-mode using the derived key.

  .. image:: docs/immutable/images/encrypt/encrypt.png

* Now you have the ciphertext.
* That was exciting right?


.. note::

   * Tahoe always uses a nonce of all NULs
   * It uses an increment-by-one counter function
   * If you ever encrypt different data with the same AES128 key and nonce, you lose
   * As just mentioned, Tahoe derives the key from the content so it only ever use a key with one dataset
   * At this point we have confidentiality.
   * This is really one of the most standard pieces of the scheme.

----

Ciphertext Hash
===============

* Hash the whole ciphertext to get the "ciphertext hash".
* A reader can use this later as the simplest way to verify **integrity** of the data.
* The downside of the simplicity is that only integrity the *complete* data can be verified

  * You can't download the first half and check that.

.. image:: docs/immutable/images/ciphertext-hash/ciphertext-hash.png

.. note::

   * Hash the whole ciphertext to get the "ciphertext hash".
   * A reader can use this later as the simplest way to verify integrity of the data.
   * The downside of the simplicity is that only integrity the *complete* data can be verified

     * For example, you can't download the first half and check that.

----

Segment
=======

* The "complete data" requirement can be eliminated at the cost of a little more complexity.
* Divide the ciphertext into segments of the chosen segment size.
* The last segment might be short.
  That's okay.

.. image:: docs/immutable/images/segment/segment-ciphertext.png

.. note::
   * The "complete data" requirement can be eliminated at the cost of a little more complexity.
   * Divide the ciphertext into segments of the chosen segment size.
   * The last segment might be short.
     That's okay.

----

Ciphertext Hash Tree - 1/2
==========================

Hash each segment separately.

.. image:: docs/immutable/images/ciphertext-hash-tree/ciphertext-hashes.png


.. note::

   * Hash each segment separately.
   * The integrity of each segment can now be verified using each of these digests.

----

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

----

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

----

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

----

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

----

URI Extension
=============

* All of the encoding parameters
* The "ciphertext hash"
* The Ciphertext Hash Tree root
* The Share Hash tree root


.. code::

  codec_name:3:crs,codec_params:11:131072-10-3,crypttext_hash:29:.},\ETX\169Pz.\236
  \245Uh\133S\147\162\STX\157$\DC3\148\153re\161\162Z\239\198,crypttext_root_hash:3
  0:>#\232\SYN\tYJ3\137Oed\225\DC4\139\189z\NUL\136\212,J\203s\238\174\213\156\NUL\
  157,needed_shares:2:40,num_segments:2:30,segment_size:2:20,share_root_hash:29:.},
  \ETX\169Pz.\236\245Uh\133S\147\162\STX\157$\DC3\148\153re\161\162Z\239\198,size:2
  :10,tail_codec_params:10:65536-10-3,total_shares:2:50,


.. note::

   * All of the encoding parameters
   * The "ciphertext hash"
   * The Ciphertext Hash Tree root
   * The Share Hash tree root

----

Shares
======

Concatenate these and you have one share:

* The encoding parameters
* The blocks for one share
* The ciphertext hash tree
* The block hash tree
* (Some of) The share hash tree
* The URI extension

----

Capability
==========

* URI:CHK:<encoded encryption key>:<encoded URI extension hash>:<required>:<total>:<application data size>
* The encryption key allows decryption and supports confidentiality.
* The URI extension hash provides integrity for the URI extension.
* The URI extension contains the share hash tree root hash which provides integrity for all of the blocks
  (and therefore all of the segments).

----


The End
=======

* Specification-in-progress: https://gitlab.com/exarkun/chk.hs/-/blob/master/docs/specification.rst
* Haskell Implementation: https://gitlab.com/exarkun/chk.hs
* Python Implementation: https://github.com/tahoe-lafs/tahoe-lafs/tree/master/src/allmydata/immutable

Questions?


