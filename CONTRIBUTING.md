# Contributing to SeatXray

Thank you for your interest in contributing to SeatXray. This document outlines the process for reporting bugs, suggesting features, and submitting code changes.

## Bug Reports

When reporting a bug, please include:

1.  **Title**: Clear and descriptive.
2.  **Reproduction Steps**: Detailed actions to reproduce the issue.
3.  **Expected vs. Actual Behavior**: What should have happened vs. what happened.
4.  **Environment**: OS version, App version.
5.  **Screenshots/Logs**: Any relevant visual aids or error logs.

## Feature Requests

Please provide:

1.  **Goal**: What you want to achieve.
2.  **Use Case**: Why this feature is necessary.
3.  **Proposed Solution**: How you envision it working.

## Development Workflow

1.  **Fork** the repository.
2.  **Clone** your fork.
3.  **Branch** for your changes (e.g., `fix/ui-alignment`, `feat/new-language`).
4.  **Commit** with descriptive messages.
5.  **Pull Request** to the `main` branch.

### Environment Setup

Refer to [README.md](README.md#development).
Requirements: Python 3.12+, Flutter (for Flet build).

## Code Style

-   Follow **PEP 8** for Python.
-   Use type hints.
-   Write comments for complex logic.

## Adding a New Language

To add support for a new language (e.g., French `fr`), you must modify the following four components.

### 1. Translation File

Create a new JSON file in `src/assets/locales/`.
*   Path: `src/assets/locales/fr.json`
*   Copy the structure from `en.json` and translate all values.

### 2. Airport Database

Create a specific directory and file for airport names.
*   Path: `src/assets/locales/fr/airports.json`
*   Format: List of airport objects. See `src/assets/locales/en/airports.json` for reference.

### 3. Settings UI

Update the language selection dropdown in `src/views/settings_view.py`.
Add your new option to the `ft.Dropdown` configuration:

```python
ft.dropdown.Option("fr", "Français (French)")
```

### 4. Currency & formatting

Update `src/utils/i18n.py` to define the default currency and formatting rules for the new locale.
*   Update `get_default_currency`: Map `fr` to `EUR`.
*   Update `format_currency`: Ensure appropriate symbol usage if not already present.

## License

Contributed code will be licensed under the project's **AGPL-3.0** license.
