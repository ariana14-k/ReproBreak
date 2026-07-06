<p align="center">
  <img src="images/logo.png" alt="ReproBreak logo" width="650" />
</p>

---

ReproBreak is a dataset of reproducible web locator breaks, mined from real-world open-source projects that use Cypress or Playwright for GUI testing. It contains 9,572 locator changes from 359 analyzed repositories and 449 locator breaks that can be re-executed and confirmed in Docker environments. The dataset supports research on test fragility, locator robustness, and automated test repair.

This is the artifact of the paper "ReproBreak: A Dataset of Reproducible Web Locator Breaks" (ASE 2026). The archival version is available on Zenodo: <https://doi.org/10.5281/zenodo.21171968>.

---

## 1. Getting Started

Setup takes less than 30 minutes. Most of that is the database download.

### 1.1 What the artifact contains

- The dataset: a 1.0 GB SQLite database, `data/ReproBreak.db`, downloaded separately.
- `reproduce.py`: reproduces any of the 449 locator breaks in a Docker environment.
- `smoke_test.py`, `verify_claims.py`, `run_reduced_experiment.py`: validation scripts, see Section 2.
- The three-phase pipeline that built the dataset and the analysis scripts used for the paper, see Sections 5 and 6.

### 1.2 Requirements

Python 3.11 or newer, git, and a running Docker daemon. Reproductions need about 30 GB of free disk space and internet access, because they clone GitHub repositories and pull Docker base images.

### 1.3 Install

**Step 1: get the artifact.** Download it from the Zenodo record, or clone the development mirror.

```bash
unzip reprobreak-code.zip -d ReproBreak && cd ReproBreak
# or: git clone https://github.com/rub-sq/ReproBreak && cd ReproBreak
```

**Step 2: download the database** from the same Zenodo record and unpack it into `data/`:

```bash
unzip ReproBreak-db.zip -d data/
```

**Step 3: install the dependencies.** With [uv](https://docs.astral.sh/uv/), all versions are pinned by `uv.lock`:

```bash
uv sync
```

<details>
<summary>Using pip instead</summary>

```bash
pip install -e .
```

Then start the scripts with `python` instead of `uv run`.

</details>

<details>
<summary>Using the artifact container instead (no local Python needed)</summary>

The scripts can also run inside a container, built from [Dockerfile.artifact](Dockerfile.artifact). The container controls the host Docker daemon through the mounted socket. Because of that, the artifact directory must be mounted at the same absolute path inside the container:

```bash
docker build -f Dockerfile.artifact -t reprobreak .
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD:$PWD" -w "$PWD" reprobreak smoke_test.py
```

Replace `smoke_test.py` with any script and its arguments. On Linux, your user needs access to `/var/run/docker.sock`, which usually means being in the `docker` group.

</details>

### 1.4 Smoke test

```bash
uv run smoke_test.py
```

The test finishes in seconds. Expected output:

```text
==================================================
  ReproBreak smoke test
==================================================
Python dependencies
  [PASS] import docker
  [PASS] import git
  [PASS] import unidiff
  [PASS] import tqdm
  [PASS] import pandas
Git CLI
  [PASS] git available (git version 2.x.x)
Dataset
  [PASS] database file exists: data/ReproBreak.db
  [PASS] repository: 359 rows (expected 359)
  [PASS] locator_change: 9572 rows (expected 9572)
  [PASS] locator_break: 449 rows (expected 449)
  [PASS] reproduce_files: 8 rows (expected 8)
Docker
  [PASS] Docker daemon reachable
==================================================
SMOKE TEST PASSED
```

Without Docker, `uv run smoke_test.py --skip-docker` checks only the dataset. Reproductions are not possible without Docker.

### 1.5 First reproduction

To see one locator break live, reproduce the example from Figure 4 of the paper. The first run of a project clones its repository and builds a Docker image, which takes 15 to 45 minutes. Later runs for the same commit reuse the cached image and take a few minutes.

```bash
uv run reproduce.py --locator_id 1224 --mode reproduce_break   # expected: ❌ Test failed!
uv run reproduce.py --locator_id 1224 --mode fixed             # expected: ✅ Test passed successfully!
```

---

## 2. Reproducing the Paper's Claims

Run all commands from the artifact root directory.

### 2.1 Claims supported by the artifact

| # | Claim | How to verify | Expected result |
|:--|:---|:---|:---|
| C1 | Dataset scale: 359 analyzed repositories, 9,572 locator changes in 211 of them, 449 reproducible breaks | `uv run verify_claims.py` | `ALL CHECKS PASSED`, seconds |
| C2 | Table 2 of the paper: locator changes per framework. Playwright 4,186 in 111 projects, Cypress 4,026 in 86, both 1,360 in 14 | `uv run verify_claims.py` | `ALL CHECKS PASSED`, seconds |
| C3 | Table 1 of the paper, columns #Lc and #Lb: angular-slickgrid 344/258, openmct 271/48, koenig 264/93, playwright 399/50 | `uv run verify_claims.py` | `ALL CHECKS PASSED`, seconds |
| C4 | Each of the 449 locator breaks is reproducible: the test passes with the new locator and fails with the old one | `uv run reproduce.py --locator_id <ID> --mode fixed`, then `--mode reproduce_break`. For larger scopes see Section 2.3 | Fixed mode passes, break mode fails |

`uv run reproduce.py --list` prints the 449 reproducible break IDs, grouped by repository.

The third mode, `overwrite`, runs the tests without touching the locator or the checkout. After every run the script prints the path of the test file. You can edit the locator there, for example to try a repair, and validate it with another run in `overwrite` mode.

### 2.2 Claims not directly supported by the artifact

- **Table 1, columns #Lc_valid (580) and #Lnb (131).** These columns count all inspected locator changes and the non-breaking ones. They were computed from the Phase 2 run outputs, which are not part of the shipped dataset. The database stores the 449 confirmed breaks only. Recomputing the two columns means re-running Phase 2 for the four projects, which takes several days. See Section 5.
- **Re-mining all 359 repositories.** A full Phase 1 run takes weeks, and the source repositories keep evolving past the cut-off date of the dataset. The mining pipeline itself can be tried on a single repository in a few minutes. See Section 5.
- **Table 2 denominators (189 Playwright, 154 Cypress, 16 both).** The framework classification of all analyzed repositories was computed during test-file detection in Phase 1 and is not persisted in the database. The database contains the classification only for repositories with locator changes.

### 2.3 Reduced and full scope

| Scope | Command | Time |
|:---|:---|:---|
| Claims check | `uv run verify_claims.py` | seconds |
| One break in both modes | `uv run reproduce.py --locator_id 1224 --mode fixed` and `--mode reproduce_break` | 20 to 50 minutes on first run, minutes afterwards |
| Reduced experiment: 8 curated breaks, two per project | `uv run run_reduced_experiment.py` | 2 to 4 hours |
| Full scope: all 449 breaks | `uv run run_reduced_experiment.py --all` | several days |

The reduced experiment validates two breaks per project in both modes and prints progress and a summary table. Each pair shares a commit, so every project image is built only once. Docker images are cached per commit. If you need the disk space afterwards, remove them with `docker image prune -a`. Careful: that removes all unused images on your machine.

---

## 3. Dataset Documentation

### 3.1 Schema

The dataset is a relational SQLite database. The schema is in [database/schema.sql](database/schema.sql) and corresponds to Figure 3 of the paper.

**`repository`** — one row per analyzed repository.
| Column | Description |
|:---|:---|
| `name` (PK) | GitHub repository in `owner/repo` form |

**`test_file`** — GUI test files detected in the latest commit of each repository.
| Column | Description |
|:---|:---|
| `file_path` (PK) | Path of the test file, relative to the repository root |
| `repository_name` (PK, FK) | Owning repository |
| `number_of_tests` | Number of test cases in the file |

**`git_commit`** — version history of the analyzed repositories.
| Column | Description |
|:---|:---|
| `sha` (PK) | Commit hash |
| `repository_name` (PK, FK) | Owning repository |
| `commit_date` | Commit date, `YYYY-MM-DD` |
| `previous_sha` | Parent commit, so both versions of a change can be checked out |

**`test_file_commit`** — which commits modified which test files.
| Column | Description |
|:---|:---|
| `test_file_path` (PK, FK) | Modified test file |
| `commit_sha` (PK, FK) | Commit that modified it |
| `repository_name` (PK, FK) | Owning repository |

**`locator_change`** — the core table, one row per mined locator change.
| Column | Description |
|:---|:---|
| `id` (PK) | Locator change ID, used by `reproduce.py --locator_id` |
| `old_locator` | Locator call before the change, for example `cy.get('.btn-action')` |
| `new_locator` | Locator call after the change |
| `line_no` | Line of the new locator in the test file at `commit_sha` |
| `framework` | `cypress` or `playwright` |
| `repository_name` (FK), `commit_sha` (FK), `test_file_path` (FK) | Where the change occurred |

**`locator_break`** — the 449 validated locator breaks.
| Column | Description |
|:---|:---|
| `locator_change_id` (PK, FK) | The validated locator change |
| `reproduce_files_id` (PK, FK) | The reproduction environment used to validate it |

**`reproduce_files`** — reproduction environments, 8 rows covering the 4 reproduced projects.
| Column | Description |
|:---|:---|
| `id` (PK) | Environment ID |
| `json` | JSON object mapping file names, `Dockerfile` and `run_tests.sh`, to their content |
| `instructions` | Optional free-text notes |

### 3.2 Provenance

The dataset is derived from the [E2EGit dataset](https://doi.org/10.1109/MSR66628.2025.00121) of open-source web applications with end-to-end GUI test suites. From it, we selected the 374 repositories that use Cypress or Playwright: 191 with Playwright and 183 with Cypress. 15 of them were no longer available on GitHub, so 359 repositories were analyzed, and 211 of those contain locator changes. We mined the full git history of every analyzed repository. The mining pipeline is described in Section 2.2 of the paper. The cut-off date is April 21, 2026. The four projects with reproduction environments are ghiscoding/angular-slickgrid, nasa/openmct, tryghost/koenig, and microsoft/playwright.

### 3.3 Ethical and legal statements

All data comes from public GitHub repositories. The database stores commit hashes, commit dates, file paths, locator code fragments, and Dockerfiles and shell scripts written by the authors. It contains no personal information: no author names, no e-mail addresses, no commit messages. The mined projects remain under their own open-source licenses. This artifact is released under the [MIT license](LICENSE). No human subjects are involved.

### 3.4 Storage requirements

| Item | Size |
|:---|:---|
| `ReproBreak-db.zip` download | ~375 MB |
| `data/ReproBreak.db` unpacked | 1.0 GB |
| Per-project reproduction, clone plus Docker image | ~2–8 GB |
| Recommended free disk space | ≥ 30 GB |

---

## 4. Usage Scenarios

Beyond reproducing the paper, ReproBreak supports the research directions from Section 4 of the paper:

1. **Locator robustness techniques.** Generate alternative locators for the elements behind `locator_change.old_locator` and check whether they survive the application change. `reproduce.py --mode overwrite` runs your modified test file against the updated application.
2. **Fragility score assessment.** `categorize_locators.py` classifies locators by type and reports type transitions across the 9,572 changes. This is a starting point for adapting fragility metrics to Cypress and Playwright.
3. **Locator repair approaches.** For each of the 449 breaks, reinsert the old locator with `--mode reproduce_break`, let your tool propose a repair, apply it to the printed test file path, and validate with `--mode overwrite`. The ground-truth repair is `locator_change.new_locator`.
4. **NL-based testing robustness.** Convert the broken tests into natural-language representations and check whether the abstraction avoids the break, using the same reproduction environments.

---

## 5. Building the Dataset from Scratch (optional)

<details>
<summary>Click to expand</summary>

The shipped database covers 359 repositories. To extend or rebuild it:

### Phase 1 — Mine locator changes

```bash
uv run create_dataset.py [owner/repo ...]
```

Without arguments, all repositories in `REPO_LIST` in `config.py` are mined, which takes weeks. With arguments, only the given repositories are mined. For example, `uv run create_dataset.py ghiscoding/angular-slickgrid` takes minutes and demonstrates the full mining pipeline. Each repository is cloned, its GUI test files and their commit history are identified, and locator changes are extracted from the diffs. Results are stored in a new SQLite database under `output/`, together with `overview.csv` and `error_overview.csv` summaries.

Key settings in `config.py`: `REPO_LIST`, `START_WITH_CLEAN_DB`, `STOP_ON_ERROR`, and `DELETE_REPO_AFTER_ANALYZE`. Set the last one to `True` to remove each clone after mining, otherwise the clones can consume a lot of storage.

### Phase 2 — Verify reproducibility

Place a `Dockerfile` and a test runner script `run_tests.sh` at `data/reproduction_files/repos/<repo-name>/`. Then run:

```bash
uv run create_reproducible_dataset.py <owner/repo>
```

This clones the repository and iterates through all commits containing a locator change. For each commit, it:
1. Builds a Docker image for the commit.
2. Runs each affected test file via `/run_tests.sh`. If the tests pass, it takes each locator change in the file, replaces the locator with its old value, and re-runs the tests. If they now fail, the change is a reproducible break. If they still pass, it is non-breaking.

Results are stored under `data/reproduction_files/repos/<repo-name>/results/<run_number>/`. Summarize them with:

```bash
uv run analyze_results.py <repo_name> <run_number>   # one run
uv run analyze_results.py <repo_name>                # all runs of a repository
```

### Phase 3 — Save results

```bash
uv run save_reproduction.py <owner/repo>
```

Reads the results of each run in order and inserts the reproduction files and the confirmed locator breaks into the database.

</details>

---

## 6. Project Structure

```text
ReproBreak/
├── README.md                        # This file
├── LICENSE                          # MIT
├── reproduce.py                     # Reproduce a locator break (--list, 3 modes)
├── smoke_test.py                    # Environment and dataset smoke test
├── verify_claims.py                 # Recompute the paper's numbers from the database
├── run_reduced_experiment.py        # Validate a subset (or --all) of the breaks
├── create_dataset.py                # Phase 1: mine locator changes
├── create_reproducible_dataset.py   # Phase 2: verify reproducibility
├── save_reproduction.py             # Phase 3: store results in the database
├── analyze_results.py               # Summarize Phase 2 runs
├── analyze_locator_changes.py       # Categorize changes (structural vs. assertion)
├── categorize_locators.py           # Classify locator types
├── helpers.py                       # Mining internals: test detection, diff parsing
├── repository_model.py              # Data classes
├── export.py                        # CSV overviews for Phase 1
├── config.py                        # Global configuration (paths, REPO_LIST)
├── Dockerfile.artifact              # Container image for the scripts
├── package_artifact.sh              # Build the archival artifact package
├── database/
│   ├── schema.sql                   # SQLite schema
│   └── database.py                  # Database access helpers
└── data/
    ├── ReproBreak.db                # Dataset (download separately, Section 1.3)
    └── reproduction_files/          # Reproduction workspaces (created on use)
```

---

## 7. License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
