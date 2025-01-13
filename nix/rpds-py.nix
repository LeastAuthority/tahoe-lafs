{
  stdenv,
  lib,
  buildPythonPackage,
  cargo,
  fetchPypi,
  pytestCheckHook,
  pythonOlder,
  rustc,
  rustPlatform,
  libiconv,
  python,
  ...
}:

buildPythonPackage rec {
  pname = "rpds-py";
  version = "0.18.1";
  format = "pyproject";

  disabled = pythonOlder "3.8";

  src = fetchPypi {
    pname = "rpds_py";
    inherit version;
    hash = "sha256-3Ei0edVAdwyBH70eubortmlRhj5Ejv7C4sECYlMo6S8=";
  };

  cargoDeps = rustPlatform.fetchCargoTarball {
    inherit src;
    name = "${pname}-${version}";
    hash = "sha256-caNEmU3K5COYa/UImE4BZYaFTc3Csi3WmnBSbFN3Yn8=";
  };

  nativeBuildInputs = [
    rustPlatform.cargoSetupHook
    rustPlatform.maturinBuildHook
    cargo
    rustc
  ];

  buildInputs = lib.optionals stdenv.hostPlatform.isDarwin [ libiconv ];

  # Without this, when building for PyPy, `maturin build` seems to fail to
  # find the interpreter at all and then fails early in the build process with
  # an error saying "unsupported Python interpreter".  We can easily point
  # directly at the relevant interpreter, so do that.
  maturinBuildFlags = [ "--interpreter" python.executable ];

  nativeCheckInputs = [ pytestCheckHook ];

  pythonImportsCheck = [ "rpds" ];

  meta = with lib; {
    description = "Python bindings to Rust's persistent data structures (rpds";
    homepage = "https://pypi.org/project/rpds-py/";
    license = licenses.mit;
    maintainers = with maintainers; [ fab ];
  };
}
