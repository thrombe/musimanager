{ pkgs ? import <nixpkgs> {}, unstable ? import <nixos-unstable> {}, serde-git, phrydy-git, pkgs-eb354ebf0 }:

let
  serde = pkgs.python310Packages.buildPythonPackage {
    name = "serde";
    src = serde-git;
    propagatedBuildInputs = with pkgs.python310Packages; [
      pytest
      mock
    ];
  };
  # - [Packaging/Python - NixOS Wiki](https://nixos.wiki/wiki/Packaging/Python)
  phrydy = pkgs-eb354ebf0.python310Packages.buildPythonPackage {
    name = "phrydy";
    src = phrydy-git;

    # tests require a bunch more dependencies which also requre a bunch more dependencies
    doCheck = false;

    propagatedBuildInputs = with pkgs-eb354ebf0.python310Packages; [
      ansicolor
      # - [python310Packages.mediafile](https://www.nixhub.io/packages/python310Packages.mediafile)
      mediafile
      typing-extensions
    ];
  };
in
pkgs.mkShell {
    packages = with pkgs; [
      (python310.withPackages(ps: with ps; [
        toml
        ytmusicapi
        pillow
        wcwidth
        numpy
        pynput
        ueberzug

        serde
      ]))
      phrydy

      unstable.yt-dlp
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

      unstable.cargo
      unstable.rustc
  ];
}
