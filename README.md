# Si nano Factory

> **Two-Dimensional World** — AI-driven multiscale platform for functionalised silica nanoparticles.

[![CI](https://github.com/mycolay/si-nano-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/mycolay/si-nano-factory/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Status: Pre-Alpha](https://img.shields.io/badge/status-pre--alpha-orange.svg)]()

End-to-end pipeline for the design, screening, and *in-silico* validation of
orthogonally functionalised SiO₂ nanoparticles. Combines GPU-accelerated DFT,
equivariant ML potentials (MACE), molecular dynamics, and a translation layer
that produces ready-to-execute synthesis recipes for the wet lab.

**Status.** Phase 0 / Pre-Alpha. The HBM4 capillary-underfill PoC runs
end-to-end (see [`prestart/HBM4_underfill_PoC/`](../prestart/HBM4_underfill_PoC/)).
The platform itself is being assembled in this repo.

## Philosophy

> *Уся хімія відбувається на поверхні. Це двовимірний світ.*

The `Surface` object is first-class throughout the schema; the bulk core is a
boundary condition (see [ARCHITECTURE.md ADR-001](docs/ARCHITECTURE.md)). Every
numerical value carries a `ProvenanceLabel` (`measured` / `model_based` /
`literature` / `assumed`); the schema structurally prevents presenting model-
based extrapolations as measurements.

## Documents (read in this order)

| Document | What it answers |
|---|---|
| [docs/MASTER_PROMPT.md](docs/MASTER_PROMPT.md) | What we're building and why |
| [docs/00_TZ.md](docs/00_TZ.md) | Technical Specification v0.2 (16 sections, ~1k lines) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | C4 diagrams, Protocol contracts, 8 ADRs |
| [docs/DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md) | How to set up your dev box (cold start ≤ 30 min) |

## Quick start

```bash
# Prereqs: Windows 11 + WSL2 Ubuntu 24.04 + NVIDIA driver 550+ + Docker Desktop.
git clone https://github.com/mycolay/si-nano-factory
cd si-nano-factory

# 1. Service stack (Postgres + MinIO + Prefect + MLflow)
docker compose up -d

# 2. Python env
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev,chem]"

# 3. Smoke
factory --help
factory version
pytest -m smoke
```

Full setup: [docs/DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md).

## Roadmap (high-level)

| Phase | Months | Deliverable |
|---|---|---|
| 0 | M0–M1 | TZ + Architecture + Dev Setup ✅ |
| 1 | M1–M3 | Module 1 (core schema) + UC-1 regression on new API |
| 1.5 | M3.5–M4 | Cardboard prototype with І. Мельник (UX freeze) |
| 2 | M4–M6 | Modules 2 + 3 basic; UC-2 (REE) + UC-3 (heavy metals); v0.5 release |
| 3 | M6–M9 | AL Watchdog; UC-4; first wet-lab handoff |
| 4 | M9–M12 | v1.0 public release; Q1 paper submission |

Full roadmap: [docs/00_TZ.md §10](docs/00_TZ.md).

## License

Apache 2.0. See [LICENSE](LICENSE).

The platform releases `ip_protected` recipes after a 6-12 month patent-disclosure
window (see [ARCHITECTURE.md ADR-003](docs/ARCHITECTURE.md)).

## Citation

A `CITATION.cff` file will be added at v0.5 release. For now, please cite
the underlying tools you actually use (RDKit, ASE, MACE, LAMMPS, Prefect).

## Acknowledgements

- **Domain expertise:** Dr. Inna Melnyk (IGT SAS / Chuiko Institute).
- **Open-source giants:** ASE, RDKit, MACE, LAMMPS, GPU4PySCF, Packmol, MDAnalysis,
  Prefect, MLflow, Pydantic.
