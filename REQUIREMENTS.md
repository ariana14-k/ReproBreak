# Requirements

## Architecture

The artifact is pure Python and architecture independent. It was tested on macOS with Apple Silicon (arm64) and Docker 28. The Docker base images used by the reproduction environments are multi-arch, so x86-64 Linux is expected to work as well. Windows is untested. The scripts assume a Unix shell and the standard Docker socket.

## Software

| Requirement | Version | Purpose |
|:---|:---|:---|
| Python | ≥ 3.11 | Runs the scripts |
| [uv](https://docs.astral.sh/uv/) (recommended) or pip | latest | Installs the pinned dependencies |
| Git CLI | any recent | Clones the projects under reproduction |
| Docker | running daemon | Builds and runs the reproduction environments |
| unzip | any | Unpacks the database |

Machine-readable dependency files: [pyproject.toml](pyproject.toml) lists the direct dependencies, [uv.lock](uv.lock) pins the full resolution, and [Dockerfile.artifact](Dockerfile.artifact) builds a containerized runtime.

## Hardware

| Resource | Recommendation |
|:---|:---|
| RAM | ≥ 8 GB. The reproduction containers run a web application plus a browser |
| Disk | ≥ 30 GB free. See README, Section 3.4 |
| CPU | Any commodity multi-core CPU. No GPU or special peripherals |

## Network

Internet access is required. It is part of how the artifact works:

- The database is downloaded once from the archival record (about 375 MB).
- The Python dependencies are installed once. This is not needed with the artifact container.
- Each reproduced project is cloned from GitHub once.
- The first image build of each project commit pulls base images and project dependencies. Later runs use the cache.

No commercial services, accounts, or API keys are needed.
