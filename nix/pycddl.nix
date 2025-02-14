{
  lib,
  pythonOlder,
  fetchPypi,
  buildPythonPackage,
  rustPlatform,
  pytestCheckHook,
  psutil,
  cbor2,
  hypothesis,
  python,
  ...
}:

buildPythonPackage rec {
  pname = "pycddl";
  version = "0.6.3";
  pyproject = true;

  disabled = pythonOlder "3.8";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-lVybSr+QvyepdTZfiTjqU0ENu6TT87ZZXIECBA8nMV4=";
  };

  # Without this, when building for PyPy, `maturin build` seems to fail to
  # find the interpreter at all and then fails early in the build process with
  # an error saying "unsupported Python interpreter".  We can easily point
  # directly at the relevant interpreter, so do that.
  maturinBuildFlags = [ "--interpreter" python.executable ];

  nativeBuildInputs = with rustPlatform; [
    maturinBuildHook
    cargoSetupHook
  ];

  postPatch = ''
    # We don't place pytest-benchmark in the closure because we have no
    # intention of running the benchmarks.  Make sure pip doesn't fail as a
    # result of it being missing by removing it from the requirements list.
    sed -i -e /pytest-benchmark/d requirements-dev.txt

    # Now that we've gotten rid of pytest-benchmark we need to get rid of the
    # benchmarks too, otherwise they fail at import time due to the missing
    # dependency.
    rm tests/test_benchmarks.py
  '';

  cargoDeps = rustPlatform.fetchCargoTarball {
    inherit src;
    name = "${pname}-${version}";
    hash = "sha256-VpJ/PLAwwuakwsNAtLDdWGXCxl6jGMTvsEhzIHk6a0g=";
  };

  nativeCheckInputs = [
    hypothesis
    pytestCheckHook
    psutil
    cbor2
  ];

  disabledTests = [
    # flaky
    "test_memory_usage"
  ];

  pythonImportsCheck = [ "pycddl" ];

  meta = with lib; {
    description = "Python bindings for the Rust cddl crate";
    homepage = "https://gitlab.com/tahoe-lafs/pycddl";
    changelog = "https://gitlab.com/tahoe-lafs/pycddl/-/tree/v${version}#release-notes";
    license = licenses.mit;
    maintainers = [ maintainers.exarkun ];
  };
}
