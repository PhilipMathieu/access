# Contributing to Access

Thank you for your interest in contributing to the Access project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Quality Tools](#code-quality-tools)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Security](#security)

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bug fix
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.10
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/PhilipMathieu/access.git
cd access

# Install dependencies with uv (recommended)
uv sync --all-groups

# Or with pip
pip install -e ".[dev]"
```

### Installing Pre-commit Hooks

We use pre-commit hooks to ensure code quality. Install them once after cloning:

```bash
uv run pre-commit install
```

Now the hooks will run automatically on every commit. To run them manually on all files:

```bash
uv run pre-commit run --all-files
```

## Code Quality Tools

This project uses several tools to maintain code quality:

### Formatting

- **Black**: Opinionated Python code formatter
- **isort**: Import statement organizer
- **Prettier**: For Markdown, JSON, and YAML files

Run formatting:
```bash
# Format Python code
uv run black src/ tests/

# Sort imports
uv run isort src/ tests/

# Or let pre-commit handle it
uv run pre-commit run --all-files
```

### Linting

- **Ruff**: Fast modern Python linter
- **mypy**: Static type checker
- **Bandit**: Security issue scanner

Run linters:
```bash
# Lint with Ruff
uv run ruff check src/ tests/

# Type check with mypy
uv run mypy src/

# Security scan with Bandit
uv run bandit -r src/
```

### Security Scanning

- **pip-audit**: Dependency vulnerability scanner
- **Bandit**: Static code security analysis

Run security checks:
```bash
# Scan dependencies for vulnerabilities
uv run pip-audit

# Scan code for security issues
uv run bandit -r src/
```

## Testing

We use pytest for testing. All tests should pass before submitting a pull request.

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_walk_times.py

# Run tests matching a pattern
uv run pytest -k "test_pattern"
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Name test functions as `test_*`
- Use descriptive test names that explain what is being tested
- Include docstrings for complex tests

Example:
```python
def test_walk_time_calculation_with_valid_input():
    """Test that walk times are calculated correctly with valid input data."""
    # Arrange
    graph = create_test_graph()

    # Act
    result = calculate_walk_times(graph, source_nodes, target_nodes)

    # Assert
    assert result is not None
    assert len(result) > 0
```

## Code Style

### General Guidelines

- **Line length**: Maximum 100 characters
- **Indentation**: 4 spaces (enforced by Black)
- **Imports**: Organized by isort (standard library, third-party, local)
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Encouraged for new code

### Docstring Style

```python
def calculate_walk_times(
    graph: nx.Graph,
    source_nodes: list[int],
    target_nodes: list[int],
    max_time: int = 30
) -> pd.DataFrame:
    """Calculate walk times between source and target nodes.

    Args:
        graph: NetworkX graph with edge weights
        source_nodes: List of source node IDs
        target_nodes: List of target node IDs
        max_time: Maximum walk time in minutes (default: 30)

    Returns:
        DataFrame with columns: source_id, target_id, walk_time

    Raises:
        ValueError: If graph is empty or nodes are invalid

    Example:
        >>> graph = load_graph("maine_walk.graphml")
        >>> times = calculate_walk_times(graph, [1, 2], [3, 4])
    """
    pass
```

### Git Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be 50 characters or less
- Reference issues and pull requests when applicable
- Use conventional commit prefixes:
  - `feat:` - New feature
  - `fix:` - Bug fix
  - `docs:` - Documentation changes
  - `style:` - Formatting changes
  - `refactor:` - Code refactoring
  - `test:` - Adding tests
  - `chore:` - Maintenance tasks

Example:
```
feat: Add H3 hexagon-based walk time calculation

- Implement calculate_hexagon_walk_times function
- Add tests for hexagon centroid mapping
- Update documentation

Closes #123
```

## Submitting Changes

### Pull Request Process

1. **Update your branch** with the latest changes from main:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Ensure all tests pass**:
   ```bash
   uv run pytest
   ```

3. **Run code quality checks**:
   ```bash
   uv run pre-commit run --all-files
   ```

4. **Push to your fork**:
   ```bash
   git push origin your-branch-name
   ```

5. **Create a pull request** on GitHub with:
   - Clear title and description
   - Reference to related issues
   - Screenshots (if applicable)
   - Test results
   - Any breaking changes noted

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No merge conflicts
- [ ] Pre-commit hooks pass
- [ ] Security scan passes

## Code Review

All pull requests require review before merging. Reviewers will check for:

- Code quality and style
- Test coverage
- Documentation completeness
- Security considerations
- Performance implications
- Breaking changes

## Security

This project has automated security scanning in place:

- **Dependabot**: Weekly automated dependency updates
- **pip-audit**: Dependency vulnerability scanning (runs weekly + on push/PR)
- **Bandit**: Security code analysis (runs weekly + on push/PR)

### Security Best Practices

When contributing, please:
- Never commit API keys, passwords, or credentials
- Use `.env` files for local secrets (excluded via `.gitignore`)
- Run `uv run pip-audit` before submitting PRs
- Follow principle of least privilege
- Validate all external inputs

## Continuous Integration

Our CI pipeline runs automatically on all pull requests:

1. **Code Quality**: Black, isort, Ruff, mypy
2. **Tests**: pytest with coverage reporting
3. **Security**: pip-audit and Bandit scans
4. **Pre-commit hooks**: All configured hooks

All checks must pass before merging.

## Development Workflow

### Typical Development Cycle

1. Create a feature branch:
   ```bash
   git checkout -b feat/my-new-feature
   ```

2. Make changes and test locally:
   ```bash
   # Edit code
   uv run pytest
   uv run pre-commit run --all-files
   ```

3. Commit changes:
   ```bash
   git add .
   git commit -m "feat: Add new feature"
   ```

4. Push and create PR:
   ```bash
   git push origin feat/my-new-feature
   ```

### Running the Pipeline Locally

Before submitting a PR, test the full pipeline:

```bash
# Run data processing pipeline
./run_pipeline.sh

# Or use Python directly
python -m src.run_pipeline
```

## IDE Configuration

### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Ruff
- Black Formatter
- EditorConfig

Settings are configured in `.vscode/settings.json` and `.editorconfig`.

### PyCharm

Settings are configured in `.editorconfig`. Enable:
- Black formatter on save
- isort on save
- Ruff linter

## Questions?

If you have questions:
- Open a GitHub issue with the `question` label
- Contact the project lead: Philip Mathieu (mathieu.p@northeastern.edu)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to Access!**
