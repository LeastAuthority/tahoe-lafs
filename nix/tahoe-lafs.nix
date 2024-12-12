let
  pname = "tahoe-lafs";
  version = "1.19.0.post1";
in
{ lib
, pythonPackages
, buildPythonPackage
, tahoe-lafs-src
}:
buildPythonPackage rec {
  inherit pname version;
  format = "pyproject";
  src = tahoe-lafs-src;
  propagatedBuildInputs = with pythonPackages; [
    attrs
    autobahn
    cbor2
    click
    collections-extended
    cryptography
    distro
    eliot
    filelock
    foolscap
    future
    hatchling
    hatch-vcs
    klein
    magic-wormhole
    netifaces
    psutil
    pyyaml
    pycddl
    pyrsistent
    pyutil
    six
    treq
    twisted
    werkzeug
    zfec
    zope_interface
  ] ++
  # Get the dependencies for the Twisted extras we depend on, too.
  twisted.passthru.optional-dependencies.tls ++
  twisted.passthru.optional-dependencies.conch;

  # The test suite lives elsewhere.
  doCheck = false;

  passthru = {
    extras = with pythonPackages; {
      tor = [
        txtorcon
      ];
      i2p = [
        txi2p-tahoe
      ];
      unittest = [
        beautifulsoup4
        html5lib
        fixtures
        hypothesis
        mock
        prometheus-client
        testtools
      ];
      integrationtest = [
        pytest
        pytest-twisted
        paramiko
        pytest-timeout
      ];
    };
  };

  postPatch =
    let
      versionFileContents = version: ''
        # This _version.py is generated by tahoe-lafs.nix.
        # TODO: We can have more metadata after we switch to flakes.
        # Then the `self` input will have a `sourceInfo` attribute telling
        __pkgname__ = "tahoe-lafs"
        real_version = "${version}"
        full_version = "${version}"
        branch = ""
        verstr = "${version}"
        __version__ = verstr
      '';
    in
      ''
        cp ${builtins.toFile "_version.py" (versionFileContents version)} src/allmydata/_version.py
        chmod 0644 src/allmydata/_version.py
      '';

  meta = with lib; {
    homepage = "https://tahoe-lafs.org/";
    description = "secure, decentralized, fault-tolerant file store";
    # Also TGPPL
    license = licenses.gpl2Plus;
  };
}
