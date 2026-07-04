# Repo Best Practices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add focused local tooling, CI, Dependabot, and security scanning configuration without changing the weather display application behavior.

**Architecture:** Keep local quality settings in `pyproject.toml`, GitHub automation in `.github/`, and human-facing notes in `README.md`. CI mirrors the repo's documented local commands so failures are easy to reproduce.

**Tech Stack:** Python 3.10, pytest, ruff, mypy, coverage.py, GitHub Actions, Dependabot, CodeQL, dependency-review-action, Gitleaks.

---

## File Structure

- Modify `pyproject.toml`: pytest, ruff, mypy, and coverage configuration.
- Create `.github/workflows/ci.yml`: standard test, lint, and type-check workflow.
- Create `.github/dependabot.yml`: scheduled dependency updates.
- Create `.github/workflows/codeql.yml`: Python CodeQL analysis.
- Create `.github/workflows/dependency-review.yml`: pull request dependency review.
- Create `.github/workflows/secret-scan.yml`: Gitleaks secret scanning.
- Modify `README.md`: short development and GitHub security settings notes.

### Task 1: Local Tooling Configuration

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Replace `pyproject.toml` with focused tool config**

```toml
[tool.pytest.ini_options]
testpaths = ["."]
python_files = ["test_*.py"]
addopts = "-ra"

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.10"
check_untyped_defs = true
files = ["weather_display"]

[[tool.mypy.overrides]]
module = ["customtkinter", "pytz", "requests"]
ignore_missing_imports = true

[tool.coverage.run]
source = ["weather_display"]
branch = true

[tool.coverage.report]
show_missing = true
skip_covered = true
```

- [ ] **Step 2: Run focused tooling checks**

Run:

```bash
./weather_venv/bin/python -m pytest
./weather_venv/bin/python -m ruff check .
./weather_venv/bin/python -m mypy weather_display
```

Expected: commands complete or reveal existing issues to fix without broad refactors.

### Task 2: CI Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Add CI workflow**

```yaml
name: CI

on:
  push:
    branches: ["main"]
  pull_request:

permissions:
  contents: read

jobs:
  checks:
    name: Tests, lint, and types
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"
          cache: "pip"

      - name: Install dependencies
        run: python -m pip install -r requirements-dev.txt

      - name: Run tests
        run: python -m pytest

      - name: Run ruff
        run: python -m ruff check .

      - name: Run mypy
        run: python -m mypy weather_display
```

- [ ] **Step 2: Validate workflow shape locally**

Run:

```bash
./weather_venv/bin/python -m pytest
```

Expected: pytest still runs with the same command CI uses.

### Task 3: Dependabot Configuration

**Files:**
- Create: `.github/dependabot.yml`

- [ ] **Step 1: Add Dependabot updates**

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

- [ ] **Step 2: Verify YAML is present**

Run:

```bash
find .github -maxdepth 3 -type f -print
```

Expected: output includes `.github/dependabot.yml`.

### Task 4: Security And Secret Scanning Workflows

**Files:**
- Create: `.github/workflows/codeql.yml`
- Create: `.github/workflows/dependency-review.yml`
- Create: `.github/workflows/secret-scan.yml`

- [ ] **Step 1: Add CodeQL workflow**

```yaml
name: CodeQL

on:
  push:
    branches: ["main"]
  pull_request:
  schedule:
    - cron: "24 3 * * 1"

permissions:
  security-events: write
  packages: read
  actions: read
  contents: read

jobs:
  analyze:
    name: Analyze Python
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: python

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

- [ ] **Step 2: Add dependency review workflow**

```yaml
name: Dependency Review

on:
  pull_request:

permissions:
  contents: read
  pull-requests: read

jobs:
  dependency-review:
    name: Dependency review
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Review dependency changes
        uses: actions/dependency-review-action@v4
```

- [ ] **Step 3: Add Gitleaks secret scan workflow**

```yaml
name: Secret Scan

on:
  push:
    branches: ["main"]
  pull_request:

permissions:
  contents: read

jobs:
  gitleaks:
    name: Gitleaks
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
```

- [ ] **Step 4: Verify workflow files exist**

Run:

```bash
find .github/workflows -maxdepth 1 -type f -print
```

Expected: output includes `ci.yml`, `codeql.yml`, `dependency-review.yml`, and `secret-scan.yml`.

### Task 5: README Development Notes

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a short development section after installation**

~~~markdown
## Development

Use the repository virtual environment for local checks:

```bash
./weather_venv/bin/python -m pytest
./weather_venv/bin/python -m ruff check .
./weather_venv/bin/python -m mypy weather_display
```

GitHub Actions runs the same checks on pushes to `main` and on pull requests.
Dependabot is configured for Python dependencies and GitHub Actions.

For repository security, the checked-in workflows run CodeQL, dependency
review, and Gitleaks secret scanning. Also enable GitHub's native secret
scanning and Dependabot alerts in the repository security settings when
available.
~~~

- [ ] **Step 2: Run final verification**

Run:

```bash
./weather_venv/bin/python -m pytest
./weather_venv/bin/python -m ruff check .
./weather_venv/bin/python -m mypy weather_display
```

Expected: all commands pass, or any existing failures are reported with the
smallest necessary fix.
