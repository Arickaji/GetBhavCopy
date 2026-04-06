# Contributing to GetBhavCopy

Thank you for your interest in contributing.

## Development Setup
```bash
git clone https://github.com/AricKaji/GetBhavCopy.git
cd GetBhavCopy
pip install -e .
pip install pre-commit
pre-commit install
```

## Branch Strategy

feature/your-feature → staging → main

Never commit directly to `main` or `staging`.

## Before Submitting a PR

Run all checks:
```bash
pre-commit run
pytest
```

Both must pass before opening a PR.

## Commit Message Format

Use conventional commits:

feat: add scheduled downloads
fix: SSL certificate error on Windows
refactor: split ui.py into modules
docs: update README changelog

## File Structure

```
src/getbhavcopy/
    ├── init.py        # version only
    ├── main.py        # entry point + headless mode
    ├── config.py          # config read/write
    ├── core.py            # download engine
    ├── logging_config.py  # logging setup
    ├── notifications.py   # desktop notifications
    ├── scheduler.py       # OS scheduler registration
    ├── settings_windows.py # settings UI
    └── ui.py              # main window
```

## Adding a New Feature

1. Create a branch: `git checkout -b feature/your-feature`
2. Add your code to the appropriate module
3. Update `README.md` changelog
4. Bump `__version__` in `__init__.py`
5. Run `pre-commit run` and `pytest`
6. Open a PR against `staging`

## Reporting Bugs

Use the Bug Report issue template. Include logs from the APPLICATION LOGS panel.
