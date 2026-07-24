# Muggy Weather Condition Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Translate the IMS `Muggy` forecast condition as `Muggy` in English and `Душно` in Russian without emitting a missing-mapping warning.

**Architecture:** Extend the existing `TRANSLATIONS` dictionaries and `WEATHER_CONDITION_MAP`; keep `translate_weather_condition(condition: Optional[str], language: str = "en") -> str` unchanged. Add one focused regression test using the real localization function and captured logs.

**Tech Stack:** Python 3.11, pytest, standard-library logging, Ruff, mypy

## Global Constraints

- Only the `Muggy` condition and its regression coverage are in scope.
- Keep the existing case-insensitive, longest-match translation behavior unchanged.
- Unknown conditions must retain the existing warning and original-string fallback behavior.
- Use `./weather_venv` for every Python tool invocation.

---

### Task 1: Support the Muggy condition

**Files:**
- Modify: `test_utils.py`
- Modify: `weather_display/utils/localization.py`

**Interfaces:**
- Consumes: `translate_weather_condition(condition: Optional[str], language: str = "en") -> str`
- Produces: `TRANSLATIONS["en"]["muggy"]`, `TRANSLATIONS["ru"]["muggy"]`, and `WEATHER_CONDITION_MAP["muggy"]`

- [ ] **Step 1: Write the failing regression test**

Add the standard-library import near the top of `test_utils.py`:

```python
import logging
```

Add this test after `test_weather_condition_handles_none_and_unmapped_text`:

```python
def test_weather_condition_translates_muggy_without_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="weather_display.utils.localization"):
        assert translate_weather_condition("Muggy", "en") == "Muggy"
        assert translate_weather_condition("Muggy", "ru") == "Душно"

    assert "No translation mapping found" not in caplog.text
```

- [ ] **Step 2: Run the regression test and verify RED**

Run:

```bash
./weather_venv/bin/python -m pytest test_utils.py::test_weather_condition_translates_muggy_without_warning -v
```

Expected: FAIL because Russian currently returns `Muggy` rather than `Душно`; the captured log also contains the missing-mapping warning.

- [ ] **Step 3: Add the minimal localization entries**

In the English weather-condition section of `TRANSLATIONS` in `weather_display/utils/localization.py`, add:

```python
'muggy': 'Muggy',
```

In the Russian weather-condition section, add:

```python
'muggy': 'Душно',
```

In `WEATHER_CONDITION_MAP`, add:

```python
'muggy': 'muggy',
```

Do not change `translate_weather_condition` or its unknown-condition fallback.

- [ ] **Step 4: Run the focused localization tests and verify GREEN**

Run:

```bash
./weather_venv/bin/python -m pytest test_utils.py::test_weather_condition_handles_none_and_unmapped_text test_utils.py::test_weather_condition_translates_muggy_without_warning -v
```

Expected: 2 passed; the unknown-condition fallback still works and `Muggy` is translated without a warning.

- [ ] **Step 5: Run full repository verification**

Run:

```bash
./weather_venv/bin/python -m pytest
./weather_venv/bin/python -m ruff check .
./weather_venv/bin/python -m mypy weather_display
```

Expected: every command exits 0 with no failures or diagnostics.

- [ ] **Step 6: Review and commit the implementation**

Run:

```bash
git diff --check
git diff -- test_utils.py weather_display/utils/localization.py
git add test_utils.py weather_display/utils/localization.py
git commit -m "fix: localize Muggy weather condition"
```

Expected: the diff contains only the regression test and the three localization entries; the commit succeeds.
