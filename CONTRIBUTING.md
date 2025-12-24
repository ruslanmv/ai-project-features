# Contributing to Aurora AI Refactor Assistant

Thank you for your interest in contributing to Aurora! This document provides guidelines and instructions for contributing to the project.

## 🎯 Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

## 🚀 Quick Start for Contributors

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/aurora-refactor.git
   cd aurora-refactor
   ```
3. **Set up the development environment**:
   ```bash
   make install-dev
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Workflow

### Before Making Changes

1. **Pull the latest changes** from the main branch:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create a new branch** for your work:
   ```bash
   git checkout -b feature/amazing-feature
   # or for bug fixes:
   git checkout -b fix/bug-description
   ```

### Making Changes

1. **Write your code** following our style guidelines (see below)
2. **Add tests** for any new functionality
3. **Update documentation** as needed
4. **Run the test suite** to ensure everything works:
   ```bash
   make test
   ```

### Code Quality Standards

Aurora maintains high code quality standards. Before committing, ensure your code passes all checks:

```bash
# Run complete audit (recommended)
make audit

# Or run individual checks:
make lint        # Ruff linter
make format      # Auto-format code
make typecheck   # MyPy type checking
make security    # Bandit security scan
make test        # Pytest test suite
```

## 📝 Code Style Guidelines

### Python Style

- **Type Hints**: All functions must have complete type hints
- **Docstrings**: Use Google-style docstrings for all public APIs
- **Line Length**: Maximum 100 characters
- **Formatting**: Code is formatted with `ruff`
- **Imports**: Sorted with `ruff` (isort rules)

### Example

```python
"""Module docstring explaining the module's purpose."""

from __future__ import annotations

import asyncio
from typing import Any

from aurora.core.logging import get_logger

logger = get_logger(__name__)


async def process_data(input_data: str, *, timeout: int = 30) -> dict[str, Any]:
    """Process input data asynchronously.

    Args:
        input_data: The data to process.
        timeout: Maximum processing time in seconds.

    Returns:
        Dictionary containing processed results.

    Raises:
        TimeoutError: If processing exceeds timeout.
        ValueError: If input_data is invalid.

    Examples:
        >>> import asyncio
        >>> result = asyncio.run(process_data("test"))
        >>> print(result)
        {'status': 'success'}
    ```
    """
    logger.info("processing_started", data_length=len(input_data))
    # Implementation here
    return {"status": "success"}
```

### Async Guidelines

- Prefer `async`/`await` for I/O-bound operations
- Use `asyncio.to_thread()` for blocking operations
- Always handle `asyncio.TimeoutError`
- Use proper async context managers (`async with`)

## 🧪 Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Mirror the source structure (e.g., `tests/core/test_config.py` for `src/aurora/core/config.py`)
- Use descriptive test names: `test_should_validate_config_when_all_fields_present`
- Use pytest fixtures for common setup
- Mark slow tests with `@pytest.mark.slow`

### Example Test

```python
"""Tests for configuration management."""

import pytest
from aurora.core.config import Settings, get_settings


class TestSettings:
    """Test suite for Settings configuration."""

    def test_should_load_settings_from_env(self, monkeypatch):
        """Settings should load from environment variables."""
        monkeypatch.setenv("WATSONX_API_KEY", "test_key_123")
        monkeypatch.setenv("WATSONX_PROJECT_ID", "test_project_123")

        settings = Settings()

        assert settings.watsonx_api_key == "test_key_123"
        assert settings.watsonx_project_id == "test_project_123"

    def test_should_validate_url_format(self):
        """Settings should reject invalid URLs."""
        with pytest.raises(ValueError, match="must start with 'https://'"):
            Settings(
                watsonx_api_key="key",
                watsonx_project_id="project",
                watsonx_url="http://invalid.com"
            )
```

## 📚 Documentation

### Code Documentation

- All public APIs must have docstrings
- Use Google-style docstring format
- Include `Args`, `Returns`, `Raises`, and `Examples` sections
- Keep examples executable and testable

### README and Guides

- Update README.md if you add new features
- Add examples for new CLI commands
- Update architecture diagrams if necessary

## 🔄 Commit Guidelines

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### Examples

```bash
feat(cli): add --output flag to save results to file

Added --output/-o flag to the refactor command, allowing users
to save refactoring results directly to a file instead of stdout.

Closes #42
```

```bash
fix(core): handle timeout in orchestrator gracefully

The orchestrator now properly catches asyncio.TimeoutError and
wraps it in AuroraTimeoutError with context information.

Fixes #123
```

## 🔀 Pull Request Process

### Before Submitting

1. **Ensure all tests pass**: `make test`
2. **Ensure code quality**: `make audit`
3. **Update documentation** as needed
4. **Rebase on main** if necessary:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

### PR Description Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran to verify your changes

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged and published
```

### Review Process

1. **Automated checks** will run on your PR
2. **Maintainers will review** your code
3. **Address feedback** promptly
4. **Keep the PR updated** with the main branch
5. Once approved, a maintainer will **merge** your PR

## 🐛 Reporting Bugs

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Update to the latest version** to see if the bug persists
3. **Reproduce the bug** with minimal steps

### Bug Report Template

```markdown
**Describe the Bug**
A clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. With input '...'
3. See error

**Expected Behavior**
What you expected to happen

**Actual Behavior**
What actually happened

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- Aurora version: [e.g., 1.0.0]

**Additional Context**
Logs, screenshots, or other relevant information
```

## 💡 Suggesting Features

We love feature suggestions! Please:

1. **Check existing issues** for similar requests
2. **Describe the problem** you're trying to solve
3. **Propose a solution** if you have one
4. **Consider implementation** complexity
5. **Think about breaking changes**

## 📜 License

By contributing to Aurora, you agree that your contributions will be licensed under the Apache License 2.0.

## 🤝 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: contact@ruslanmv.com

## 🌟 Recognition

Contributors will be recognized in:
- The project README
- Release notes
- GitHub contributors page

Thank you for contributing to Aurora! 🚀
