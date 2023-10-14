{
  description = "yaaaaaaaaaaaaaaaaaaaaa";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-23.05";
    unstable-nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    nixpkgs-eb354ebf0.url = "github:nixos/nixpkgs/a174de16edfc6aa0893530b9a95d0bd0c2a952b7";
    nixpkgs-80c24eeb9.url = "github:nixos/nixpkgs/80c24eeb9ff46aa99617844d0c4168659e35175f";

    serde-git = {
      url = "github:rossmacarthur/serde";
      flake = false;
    };
    phrydy-git = {
      url = "github:Josef-Friedrich/phrydy/2adfc4fcca3880837b0053592b3c87e8fc5011dd";
      flake = false;
    };
    jflib-git = {
      url = "github:Josef-Friedrich/jflib";
      flake = false;
    };
    mediafile-git = {
      url = "github:beetbox/mediafile/255afafd2da2febce705fe9702eaf1e4b8c437c2";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, unstable-nixpkgs, serde-git, phrydy-git, mediafile-git, nixpkgs-eb354ebf0, nixpkgs-80c24eeb9, jflib-git }:
  let
    system = "x86_64-linux";

    pkgs-eb354ebf0 = import nixpkgs-eb354ebf0 { inherit system; };
    pkgs-80c24eeb9 = import nixpkgs-80c24eeb9 { inherit system; };
    pkgs = import nixpkgs {
      inherit system;
    };
    unstable = import unstable-nixpkgs {
      inherit system;
      # - [Overlays | NixOS & Flakes Book](https://nixos-and-flakes.thiscute.world/nixpkgs/overlays)
      overlays = [
        (self: super: {})
      ];
    };
  in
  {
    devShells."${system}".default = (import ./shell.nix { inherit pkgs unstable serde-git phrydy-git mediafile-git jflib-git pkgs-eb354ebf0 pkgs-80c24eeb9; });
  };
}
