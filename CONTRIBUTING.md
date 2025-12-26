# Contributing to WebSite to Android & iOS App

Thank you for considering contributing to this project! We welcome all contributions.

## How to Contribute

### Reporting Bugs
1. Check if the bug has already been reported in [Issues](https://github.com/z1000biker/website2app/issues).
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected behavior vs. actual behavior
   - Your environment (OS, Python version, Java version)
   - Screenshots or logs if applicable

### Suggesting Features
1. Open an issue describing the feature.
2. Explain why it would be useful.
3. Provide examples of how it might work.

### Submitting Pull Requests
1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes following the code style guidelines below.
4. Test your changes.
5. Commit with clear messages: `git commit -m "Add: description of change"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Open a Pull Request against the `main` branch.

## Code Style

- **Python**: Follow PEP 8. Use `black` for formatting and `isort` for imports.
- **Line Length**: 120 characters max.
- **Docstrings**: Use Google-style docstrings for public functions.
- **Type Hints**: Encouraged for function signatures.

### Running Code Quality Tools
```bash
# Format code
black .
isort .

# Check linting
flake8 .

# Type checking
mypy .
```

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/website2app.git
   cd website2app
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Commit Message Guidelines

Use conventional commit prefixes:
- `Add:` for new features
- `Fix:` for bug fixes
- `Update:` for changes to existing features
- `Refactor:` for code refactoring
- `Docs:` for documentation changes
- `Test:` for adding or updating tests

## Questions?

Feel free to open an issue or reach out to the maintainer at sv1eex@hotmail.com.

---

Thank you for contributing! 🎉
