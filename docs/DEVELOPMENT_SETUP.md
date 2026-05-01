# Development Setup — Si nano Factory

> **Статус:** v0.1 · обов'язкове читання перед першим запуском
> **Hardware target:** Intel i9-13gen / 64 GB RAM / 1 × NVIDIA RTX 3090 (24 GB) / Windows 11 + WSL2
> **Час на cold-start:** ~30 хв з нуля до першої CLI-команди (за умови pre-pull Docker images)

---

## 0. Архітектурне рішення (нагадування з 00_TZ §1.4)

Локально на одній робочій станції. Усе через WSL2-Ubuntu всередині Windows-host'а
(тому що MACE/LAMMPS/PLUMED — Linux-native; Windows-native страждає від
залежностей CUDA-toolchain). VS Code — host-side, але всі команди виконуються
у WSL2. Згодом цей самий setup буде reused для віддалених SLURM/cloud-бекендів
(§14 ТЗ) — тому що Apptainer-образ на HPC буде клоном local Docker-образу.

```
┌─────────────────────────────────────────────────────────────┐
│  Windows 11 host                                             │
│  ┌────────────────────────┐  ┌─────────────────────────┐    │
│  │  VS Code (UI / agent)  │←→│  WSL2 Ubuntu 24.04      │    │
│  │  + Claude Code ext     │  │  + Docker Engine        │    │
│  │  + Python ext + Pylance│  │  + CUDA 12.1 toolkit    │    │
│  └────────────────────────┘  └─────────────────────────┘    │
│              │                            │                  │
│              ▼                            ▼                  │
│        nvidia-smi (host)          MACE / LAMMPS / Prefect   │
│              │                            │                  │
│              └─────────────┬──────────────┘                  │
│                            ▼                                 │
│                  RTX 3090 (CUDA shared)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Hardware & OS checklist

### 1.1 Перевірка GPU

```bash
# host (PowerShell):
nvidia-smi
# має показати CUDA 12.1+, RTX 3090, driver ≥ 550.x

# WSL2 (bash):
nvidia-smi                       # той же висновок
nvcc --version                   # nvcc 12.1
python3 -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# True, NVIDIA GeForce RTX 3090
```

Якщо `torch.cuda.is_available() == False` — переконайтесь що:
1. Windows GPU driver **NVIDIA Game Ready ≥ 550.x** (для CUDA 12.1)
2. WSL2 на **WSL kernel ≥ 5.15** (`wsl --version`)
3. У `~/.bashrc` всередині WSL: `export PATH=/usr/local/cuda-12.1/bin:$PATH`

### 1.2 Disk layout

| Місце | Призначення | Розмір (рек.) |
|---|---|---|
| `C:\ai_server\Si_моделювання\` | проєкт-репо (Windows side) | ~1 GB code+docs |
| `\\wsl$\Ubuntu-24.04\home\<user>\sinanofactory\` | WSL bind для роботи | linked to above |
| `~/sinanofactory/data/` | DVC working dir | ~50 GB raw datasets |
| `~/sinanofactory/trajectories/` | hot-tier trajectories | ~200 GB (rotate to MinIO) |
| Docker volumes (`/var/lib/docker/volumes/`) | Postgres+MinIO+MLflow data | ~100 GB |

> **Важливо:** не тримати робочі дані безпосередньо на Windows-side диску — WSL2
> через `/mnt/c/` має ~10× повільніший I/O ніж native ext4. Натомість працюємо
> з WSL native FS і робимо `git push` для синхронізації коду.

### 1.3 RAM/swap budget (рекомендоване `.wslconfig`)

`%UserProfile%\.wslconfig`:
```ini
[wsl2]
memory=48GB                # лишаємо 16 GB для Windows + GPU drivers
processors=20              # лишаємо 4 для Windows
swap=32GB                  # для випадків коли DFT-задача спам'ятала 60 GB
swapFile=D:\\wslswap.vhdx  # на швидкому SSD
localhostForwarding=true   # критично для Prefect/MLflow UI
```

Перезапустити WSL: `wsl --shutdown` у PowerShell.

---

## 2. VS Code configuration

### 2.1 Recommended extensions (`.vscode/extensions.json`)

Файл вже створений у репо; при відкритті workspace VS Code запропонує
встановити. Список і чому кожен:

| Extension | ID | Чому |
|---|---|---|
| Claude Code | `anthropic.claude-code` | агентна робота (те, що ми зараз робимо) |
| Python | `ms-python.python` | основа |
| Pylance | `ms-python.vscode-pylance` | type-checking, refactor |
| Ruff | `charliermarsh.ruff` | форматування + lint (швидше ніж black+flake8) |
| Mypy Type Checker | `ms-python.mypy-type-checker` | strict types для core/ |
| Jupyter | `ms-toolsai.jupyter` | для exploratory notebooks |
| Docker | `ms-azuretools.vscode-docker` | управління контейнерами |
| Dev Containers | `ms-vscode-remote.remote-containers` | dev container support |
| WSL | `ms-vscode-remote.remote-wsl` | seamless WSL editing |
| Remote - SSH | `ms-vscode-remote.remote-ssh` | для §14 HPC бекендів |
| GitLens | `eamodio.gitlens` | blame, history |
| GitHub Pull Requests | `github.vscode-pull-request-github` | PR review без браузера |
| Mermaid Preview | `bierner.markdown-mermaid` | діаграми в .md |
| TOML | `tamasfe.even-better-toml` | для pyproject.toml |
| YAML | `redhat.vscode-yaml` | для docker-compose, GitHub Actions |
| SQL Tools | `mtxr.sqltools` + `mtxr.sqltools-driver-pg` | postgres queries не виходячи з IDE |

### 2.2 Workspace settings (`.vscode/settings.json`)

Ключові — формат, lint, інтерпретатор:
```json
{
  "python.defaultInterpreterPath": "/home/<USER>/sinanofactory/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll.ruff": "explicit"
    }
  },
  "ruff.lint.select": ["E", "F", "I", "B", "UP", "N", "RUF", "ANN", "PTH"],
  "mypy-type-checker.args": ["--strict", "--ignore-missing-imports"],
  "files.exclude": { "**/__pycache__": true, "**/.pytest_cache": true },
  "search.exclude": { "**/.venv": true, "**/data/raw": true }
}
```

Повний файл — `.vscode/settings.json` у корені проєкту.

### 2.3 Recommended terminal layout (4 panels)

```
┌──────────────────────────┬──────────────────────────┐
│  Terminal 1: dev shell   │  Terminal 2: nvtop       │
│  (тут ви редагуєте/      │  (постійний моніторинг   │
│   запускаєте команди)    │   GPU)                   │
├──────────────────────────┼──────────────────────────┤
│  Terminal 3: btop        │  Terminal 4: docker logs │
│  (CPU/RAM)               │  -f (servce health)      │
└──────────────────────────┴──────────────────────────┘
```

Налаштовується через `tasks.json` — одна команда `Run: dev shell layout`
відкриває всі 4 panel-а. Створимо у Phase B (code skeleton).

---

## 3. Docker stack (Phase 0 deliverable)

Файл `docker-compose.yml` уже створений у репо. Запуск:

```bash
cd ~/sinanofactory
docker compose up -d
docker compose ps          # перевірка
```

### 3.1 Сервіси

| Service | Port | Призначення | Web UI |
|---|---|---|---|
| `postgres` | 5432 | metadata DB | — (DBeaver/SQLTools) |
| `minio` | 9000, 9001 | S3-сумісне об'єктне сховище | http://localhost:9001 (admin/admin) |
| `prefect-server` | 4200 | DAG-orchestration | http://localhost:4200 |
| `mlflow` | 5000 | experiment tracking | http://localhost:5000 |
| `streamlit` (опційно) | 8501 | PI dashboard | http://localhost:8501 |

### 3.2 Skip-list

Що **НЕ** в docker-compose (запускається окремо):
- LAMMPS / MACE / ORCA — натив у WSL з GPU passthrough (Docker-runtime nvidia
  ускладнює підтримку MACE pair_style; швидше натив)
- Saving traffic: Postgres data persists на named volume `sinanofactory_pg_data`
  (не зникає між `docker compose down`)

### 3.3 Reset (коли все накрилось)

```bash
docker compose down -v        # -v видалить volumes (УВАГА — повне очищення)
rm -rf data/                  # WSL-side каталоги
docker compose up -d
factory init                  # створить заново структуру DB та DVC remote
```

---

## 4. Python environment

Один `.venv` під WSL2, керований через `uv` (швидший за pip + автоматичний lock).

```bash
# в WSL2:
cd ~/sinanofactory
curl -LsSf https://astral.sh/uv/install.sh | sh    # один раз
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev,gpu]"                      # після створення pyproject.toml
```

`pyproject.toml` буде створений у Phase B (code skeleton); матиме три extras:
- `[dev]` — pytest, hypothesis, ruff, mypy, mkdocs
- `[gpu]` — torch+CUDA12.1, mace-torch, lammps-mace
- `[hpc]` — apptainer-cli, dask-jobqueue (опційно для §14)

---

## 5. Daily workflow — три типові сценарії

### 5.1 Новий use-case (UC-3 Heavy metals як приклад)

```bash
# 1. Створюємо spec
factory spec new --template=heavy-metal-sorbent \
                 --core=stober-100nm \
                 --ligands=MPTMS,APTMS \
                 --target-ion=Cu2+ \
                 -o specs/uc3_first.json

factory spec validate specs/uc3_first.json

# 2. Дешевий screening (Tier 0/1, кілька годин на CPU)
factory screen --spec=specs/uc3_first.json \
               --pool=zinc_silanes_chelators.csv \
               --top=50 \
               -o screening_uc3.csv

# 3. Дивимось результати
streamlit run sinanofactory/dashboard/screening.py
# → http://localhost:8501

# 4. Tier 2 на топ-3 (нічна задача)
factory run uc3 --candidates=screening_uc3.csv --top=3 --tier=deep-study
# Prefect UI: http://localhost:4200 — слідкуємо за прогресом

# 5. Звіт
factory recipe --run-id=<latest> -o recipes/uc3_top1.pdf
```

### 5.2 Debug failed Prefect run

```bash
# 1. Знайти run-id
factory queue --status=failed --limit=5

# 2. Логи
prefect logs <run-id>            # прямо в терміналі
# або UI: http://localhost:4200/runs/<run-id>

# 3. Replay з тим же seed
factory replay <run-id> --break-on-fail
# зупиниться у Python debugger перед exception → можна inspect

# 4. Виправили → push → CI зелений → merge → deploy
```

### 5.3 Profile slow MACE inference

```bash
# 1. Мала вибірка (10 кадрів)
factory profile mace --model=hbm4_real_model_stagetwo \
                     --frames=10 \
                     --device=cuda \
                     -o profile.json

# 2. Перегляд
nvtop                            # у другій terminal panel — бачимо utilization
# або: nsys profile -o trace python scripts/inference.py
# → відкриваємо trace у NVIDIA Nsight Systems на host
```

---

## 6. Monitoring (live during runs)

Один screen, чотири погляди:

| Що | Команда | Якщо червоний — |
|---|---|---|
| GPU memory leak | `nvtop` | restart Python; перевірити чи `del model; torch.cuda.empty_cache()` |
| OOM kill | `dmesg \| tail -20` | NFR-15 авто-fallback; якщо ні — зменшити batch_size в spec |
| Disk fill | `df -h ~/sinanofactory/` | NFR-14: запустити `factory cleanup --raw --older-than=3d` |
| Prefect agent повис | `docker compose logs -f prefect-server` | restart агент: `prefect worker start -p default` |
| Postgres slow | `docker compose exec postgres psql -U factory -c "SELECT * FROM pg_stat_activity"` | індекс на `(spec_hash)`; vacuum analyze |

Для довгих jobs (>4 год) — налаштувати **notifications**:
```bash
factory notify --on=success,fail --channel=telegram --token=$TG_TOKEN
```
(імплементація у Module 3, Phase 3.)

---

## 7. Antigravity як secondary (опційно)

Google Antigravity — окремий agentic IDE (released Q4 2025). Якщо хочете
мати його паралельно як expermentation sandbox:

| Use-case | VS Code | Antigravity |
|---|---|---|
| Звичайна розробка | ✅ primary | — |
| Інтерактивні агентні цикли | ✅ via Claude Code ext | ✅ native |
| Multi-agent orchestration (Sub-agents для self-corrected design) | можливо через Claude Code | native, але ще rough |
| GPU monitoring + WSL інтеграція | ✅ | обмежено |
| Mature Python tooling (Pylance, Ruff, Jupyter) | ✅ | гірше |

> **Pragmatic stance.** Вмикати Antigravity тільки для experimentation з
> autonomous-agent-патернами (е.g., "agent generates 100 NanoparticleSpecs
> overnight, evaluates each, ranks"). Для писання production-коду — VS Code.

Налаштування — поза scope цього doc; deferred до моменту коли реально
знадобиться (Phase 3+).

---

## 8. Перший запуск (cold-start — 30 хв)

```bash
# 0. Передумови (одноразово)
#    - Windows 11 + WSL2 Ubuntu 24.04
#    - NVIDIA driver 550+
#    - Docker Desktop з WSL2 backend
#    - VS Code + Claude Code ext

# 1. Клон
cd ~
git clone https://github.com/<your-handle>/si-nano-factory sinanofactory
cd sinanofactory

# 2. Open in VS Code (з WSL)
code .                    # → "Reopen in WSL" якщо запропонує
# Прийняти всі recommended extensions

# 3. Docker stack
docker compose up -d
# Чекаємо ~2 хв (перший pull Postgres+MinIO+Prefect+MLflow)

# 4. Python env
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev,gpu]"
# Чекаємо ~5 хв (torch+CUDA — найбільший)

# 5. Smoke test
factory --help
factory init                          # створить tables, MinIO buckets, DVC remote
pytest tests/smoke/                   # повинні всі пройти

# 6. Перевіряємо UI
# Відкриваємо у Windows-браузері:
#   http://localhost:4200       (Prefect)
#   http://localhost:5000       (MLflow)
#   http://localhost:9001       (MinIO)
```

Якщо все зелене — ви готові починати Phase 1 (Module 1 implementation).

---

## 9. Troubleshooting (FAQ)

**Q: `docker compose up` падає з "no nvidia driver"**
A: Docker Desktop потребує WSL2 nvidia-container-toolkit. Гайд:
   https://docs.nvidia.com/cuda/wsl-user-guide/

**Q: VS Code не бачить мого .venv**
A: `Ctrl+Shift+P` → "Python: Select Interpreter" → вибрати з `.venv/bin/python`.
   Якщо немає в списку — `which python` у WSL терміналі, повний шлях вставити вручну.

**Q: MACE OOM на 8000-атомній частинці**
A: NFR-15 (graceful degradation) ще не імплементовано (це Module 3, Phase 3).
   Тимчасово: уручну зменшити `batch_size` у `pyproject.toml` extras або через
   ENV `FACTORY_MACE_BATCH=1`.

**Q: Prefect job stuck у `Pending`**
A: Не запущений worker. `prefect worker start --pool=default` у окремому
   terminal panel. Або через docker-compose service `prefect-worker` (буде
   додано в Phase 1).

**Q: Чому `data/` не в git?**
A: Це DVC-керований каталог. `git status` його ігнорує (`.gitignore`).
   Sync через `dvc push` / `dvc pull`.

---

## 10. Що далі (після цього setup)

1. **Phase 0 завершено** — у вас працююче середовище.
2. **Phase 1 (Module 1):** `NanoparticleSpec` + builder + tests — наступний deliverable.
3. **Phase 1.5 (M4 Cardboard prototype):** UX-сесія з І. Мельник на
   форматі звіту — паралельно з кодом.

---

*Документ v0.1 · Si nano Factory — Two-Dimensional World*
