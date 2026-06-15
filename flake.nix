{
    description = "Python development environment";

    inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    };

    outputs = { self, nixpkgs, ... }:
        let
            pkgs_aarch = nixpkgs.legacyPackages.aarch64-darwin;
            pkgs_x86 = nixpkgs.legacyPackages.x86_64-darwin;
        in
        {
            devShells.aarch64-darwin.default = pkgs_aarch.mkShell {
                name = "rocky-hockey-python-shell-aarch64";
                buildInputs = [
                    pkgs_aarch.python3
                      pkgs_aarch."pkg-config"
                    pkgs_aarch.git
                ];
                shellHook = ''
                    if [ ! -d .venv ]; then
                        python3 -m venv .venv
                    fi

                    . .venv/bin/activate
                    python3 -m pip install --upgrade pip
                    python3 -m pip install -r requirements.txt
                '';
            };

            devShells.x86_64-darwin.default = pkgs_x86.mkShell {
                name = "rocky-hockey-python-shell-x86_64";
                buildInputs = [
                    pkgs_x86.python3
                      pkgs_x86."pkg-config"
                    pkgs_x86.git
                ];
                shellHook = ''
                    if [ ! -d .venv ]; then
                        python3 -m venv .venv
                    fi

                    . .venv/bin/activate
                    python3 -m pip install --upgrade pip
                    python3 -m pip install -r requirements.txt
                '';
            };
        };
}