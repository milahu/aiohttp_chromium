{ pkgs ? import <nixpkgs> { }
  #pkgs ? import ./. {}
}:

with pkgs;

let
  # chromium is built with llvm 17
  # nixpkgs/pkgs/applications/networking/browsers/chromium/default.nix
  #   llvmPackages_attrName = "llvmPackages_17";
  #   stdenv = pkgs.${llvmPackages_attrName}.stdenv;
  lldb = llvmPackages_17.lldb;
in

mkShell {
  shellHook = ''
    # useless?
    export PYTHONPATH="${lldb.lib}/lib/python3.11/site-packages:$PYTHONPATH"
  '';
  buildInputs = [
    gnumake
    (python3.withPackages (pp: with pp; [
      #requests
      # useless?
      lldb
    ]))
    lldb
  ];
}
