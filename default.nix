{ lib, python3Packages }:
let
  # Name, version and description are only kept in pyproject.toml.
  project = (lib.importTOML ./pyproject.toml).project;
in
python3Packages.buildPythonApplication {
  pname = project.name;
  inherit (project) version;
  pyproject = true;

  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions [
      ./pyproject.toml
      ./README.md
      ./src
      ./tests
    ];
  };

  build-system = [ python3Packages.uv-build ];
  dependencies = [ python3Packages.pillow ];
  nativeCheckInputs = [ python3Packages.pytestCheckHook ];

  meta = {
    inherit (project) description;
    mainProgram = "waybar-pokemon";
    platforms = lib.platforms.linux;
  };
}
