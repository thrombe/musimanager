{
  description = "yaaaaaaaaaaaaaaaaaaaaa";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-23.05";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    nixpkgs-eb354ebf0.url = "github:nixos/nixpkgs/a174de16edfc6aa0893530b9a95d0bd0c2a952b7";

    serde-git = {
      url = "github:rossmacarthur/serde";
      flake = false;
    };
    phrydy-git = {
      url = "github:Josef-Friedrich/phrydy/2adfc4fcca3880837b0053592b3c87e8fc5011dd";
      flake = false;
    };
    py-cui-git = {
      url = "github:jwlodek/py_cui/3a7f79cb1cfda4e5aa650a7f92ac04ef7c360e5f";
      flake = false;
    };
  };

  outputs = inputs@{...}:
    inputs.flake-utils.lib.eachSystem ["x86_64-linux"] (system: let
      pkgs = import inputs.nixpkgs {
        inherit system;
      };
      unstable = import inputs.nixpkgs-unstable {
        inherit system;
      };
      pkgs-eb354ebf0 = import inputs.nixpkgs-eb354ebf0 { inherit system; };

      serde = pkgs.python310Packages.buildPythonPackage {
        name = "serde";
        src = inputs.serde-git;
        propagatedBuildInputs = with pkgs.python310Packages; [
          pytest
          mock
        ];
      };
      py-cui = pkgs.python310Packages.buildPythonPackage {
        name = "py-cui";
        src = inputs.py-cui-git;
        doCheck = false;
        propagatedBuildInputs = with pkgs.python310Packages; [
        ];
      };
      # - [Packaging/Python - NixOS Wiki](https://nixos.wiki/wiki/Packaging/Python)
      phrydy = pkgs-eb354ebf0.python310Packages.buildPythonPackage {
        name = "phrydy";
        src = inputs.phrydy-git;

        # tests require a bunch more dependencies which also requre a bunch more dependencies
        doCheck = false;

        propagatedBuildInputs = with pkgs-eb354ebf0.python310Packages; [
          ansicolor
          # - [python310Packages.mediafile](https://www.nixhub.io/packages/python310Packages.mediafile)
          mediafile
          typing-extensions
        ];
      };
    in {
      devShells.default = pkgs.mkShell {
        nativeBuildInputs = with pkgs; [
            (python310.withPackages(ps: with ps; [
              toml
              ytmusicapi
              pillow
              wcwidth
              numpy
              pynput
              ueberzug

              serde
              py-cui
            ]))
            phrydy

            unstable.rust-analyzer
            unstable.rustfmt
            unstable.clippy
            unstable.cargo
            unstable.rustc

            # unstable.yt-dlp
            yt-dlp
            pkg-config

            mpv

            gst_all_1.gstreamer
            gst_all_1.gst-plugins-base
            gst_all_1.gst-plugins-good
            gst_all_1.gst-plugins-bad
            gst_all_1.gst-plugins-ugly
            # Plugins to reuse ffmpeg to play almost every video format
            gst_all_1.gst-libav
            # Support the Video Audio (Hardware) Acceleration API
            gst_all_1.gst-vaapi
          ];
      };
    });
}
