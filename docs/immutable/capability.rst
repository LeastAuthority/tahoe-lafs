Capability
==========

* URI:CHK:<encoded encryption key>:<encoded URI extension hash>:<required>:<total>:<application data size>
* The encryption key allows decryption and supports confidentiality.
* The URI extension hash provides integrity for the URI extension.
* The URI extension contains the share hash tree root hash which provides integrity for all of the blocks
  (and therefore all of the segments).
