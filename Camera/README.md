# Rockey Hockey Camera

## Voraussetzungen
- Rust (stable) — Rust und Cargo: https://rustup.rs
- OpenCV und die Entwicklungsheaders
	- Debian: `sudo apt install libopencv-dev pkg-config`
	- macOS: `brew install opencv` (oder über Homebrew-Links)
- Für Cross-Compilation: Docker (nur für das mitgelieferte Script)

## Schnellstart (Entwicklung)

Im Projektordner:

```bash
cargo run -- --web-ui --target-output 0.0.0.0:5005
```

- `--web-ui` startet den integrierten Webserver zur Konfiguration der Detektionsziele.
- `--target-output <ip:port>` bindet eine UDP-Interface, an das sich ein Client mit einem Subscribe-Paket anmelden kann. Danach sendet der Detector die Zielpositionen an diesen Client.

Weitere Optionen sehen Sie mit:

```bash
cargo run -- --help
```

## Cross-Compilation für Raspberry Pi (aarch64)

Das Repository enthält ein Hilfs-Skript zur Cross-Compilation mittels Docker.

1. Stellen Sie sicher, dass Docker installiert und lauffähig ist.
2. Prüfen Sie, dass das Docker-Image im `Dockerfile` mit dem Raspberry Pi kompatibel ist.
3. Führen Sie das Script aus:

```bash
./aarch64-cross.sh
```

Nach erfolgreichem Build liegt die Binary unter:

- `target/aarch64-unknown-linux-gnu/release/rockey_hockey`

Kopieren Sie diese Datei auf Ihr Gerät (z. B. mit `scp`) und führen Sie sie dort aus.

## Konfiguration / Web-UI

Die Web-UI dient zur Auswahl und Feinabstimmung der Detektionsziele. Falls Sie `--web-ui` verwenden, wird ein lokaler Webserver gestartet; die genaue URL wird beim Start geloggt.