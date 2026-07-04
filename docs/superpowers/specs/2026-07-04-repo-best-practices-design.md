# Repo Best Practices Configuration Design

## Scope

Configure this Python Raspberry Pi weather display repo with focused local
tooling and GitHub automation. Do not change application behavior, runtime
startup strategy, or old weather API-key arguments.

## Assumptions

- The repo targets Python 3.10 or newer.
- Local checks should use the existing `./weather_venv` environment.
- CI should install from `requirements-dev.txt` and run the same standard
  commands documented in `AGENTS.md`.
- GitHub native secret scanning is controlled by repository or organization
  settings, so repo config will add a CI secret scan and document that native
  secret scanning should also be enabled in GitHub settings.

## Approach

Use a focused configuration set rather than a full packaging rewrite.

- Keep `setup.py` and the current package layout.
- Expand `pyproject.toml` with pytest, ruff, mypy, and coverage settings.
- Add GitHub Actions CI for tests, linting, and type checking.
- Add Dependabot for GitHub Actions and Python dependency updates.
- Add CodeQL and dependency review for security checks.
- Add a Gitleaks workflow for repo-level secret scanning.

## Components

### Local Tooling

`pyproject.toml` will define:

- pytest discovery for root-level `test_*.py` files.
- ruff target Python version, line length, and a practical rule selection.
- mypy settings matching the existing behavior for `weather_display`.
- coverage settings for `weather_display` without enforcing a threshold.

### CI

`.github/workflows/ci.yml` will run on pushes and pull requests:

- Set up Python 3.10.
- Install development requirements.
- Run pytest, ruff, and mypy.

### Dependency Automation

`.github/dependabot.yml` will check:

- Python package updates for `requirements*.txt`.
- GitHub Actions updates.

### Security Automation

GitHub workflows will add:

- CodeQL analysis for Python.
- Dependency review on pull requests.
- Gitleaks secret scanning on pushes and pull requests.

## Verification

Run the standard local checks:

```bash
./weather_venv/bin/python -m pytest
./weather_venv/bin/python -m ruff check .
./weather_venv/bin/python -m mypy weather_display
```

If development tools are missing, install them from `requirements-dev.txt`.

## Out Of Scope

- Replacing `setup.py` with PEP 621 package metadata.
- Adding pre-commit hooks.
- Adding coverage gates.
- Changing runtime logging, cache behavior, service startup, or GUI behavior.
