{
  pkgs ? import <nixpkgs> {}
}:

let
  extraPythonPackages = rec {
    fritap = pkgs.python3.pkgs.callPackage ./nix/fritap.nix {};
  };

  python = pkgs.python3.withPackages (pythonPackages:
  (with pythonPackages; [
  ])
  ++
  (with extraPythonPackages; [
    fritap
  ])
  );

in

pkgs.mkShell rec {

buildInputs = ([
]) ++ [
  python
]
++
(with extraPythonPackages; [
    fritap
]);

}
