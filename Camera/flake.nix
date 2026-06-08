{
    description = "OpenCV dev environment";

    outputs = { self, nixpkgs }: {
        devShells.aarch64-darwin.default = nixpkgs.legacyPackages.aarch64-darwin.mkShell {
            name = "opencv-dev-shell";
            buildInputs = [
                nixpkgs.legacyPackages.aarch64-darwin.opencv
                nixpkgs.legacyPackages.aarch64-darwin.cmake
            ];
        };
    };
}