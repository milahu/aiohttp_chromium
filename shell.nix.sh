#!/bin/sh

cd "$(dirname "$0")"

export NIXPKGS_ALLOW_UNFREE=1

exec nix-shell
