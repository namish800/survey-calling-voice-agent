# Contributing to Universal Agent

Thank you for your interest in contributing to Universal Agent! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

Bug reports help us improve the project. When reporting bugs, please:

1. **Check existing issues** to see if the bug has already been reported
2. **Use the bug report template** if available
3. **Provide detailed information** about the bug:
   - Clear steps to reproduce the issue
   - Expected behavior vs. actual behavior
   - Error messages and stack traces
   - Environment details (OS, Python version, etc.)

### Suggesting Enhancements

We welcome feature suggestions! When suggesting enhancements:

1. **Check existing issues** to avoid duplicates
2. **Use the feature request template** if available
3. **Describe the enhancement** in detail:
   - What problem would it solve?
   - How would it work?
   - Why would it benefit the project?

### Pull Requests

We actively welcome your pull requests:

1. **Fork the repo** and create your branch from `main`
2. **Install development dependencies** with `pip install -e ".[dev]"`
3. **Make your changes**, following our coding conventions
4. **Add tests** for your changes
5. **Run the test suite** to ensure all tests pass
6. **Update documentation** if needed
7. **Submit a pull request** with a clear description of the changes

## Development Workflow

### Setting up the Development Environment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vaani
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

### Code Style

We follow these coding conventions:

- **Black** for code formatting (100 character line limit)
- **Flake8** for style checking
- **Type hints** for all function and method definitions
- **Docstrings** for all public modules, functions, classes, and methods

You can validate your code with:
```bash
black universalagent
flake8 universalagent
mypy universalagent
```

### Testing

We use pytest for testing:

```bash
pytest
```

For coverage reports:
```bash
pytest --cov=universalagent
```

## Component-Specific Guidelines

### Adding New AI Providers

When adding support for new AI providers:

1. Create a new connector in the appropriate component directory
2. Implement the required interfaces
3. Update the ComponentFactory to recognize the new provider
4. Add documentation for the new provider
5. Add tests for the new provider implementation

### Creating New Tools

When creating new tools:

1. Extend the ToolHolder class with your implementation
2. Register the tool in the appropriate place
3. Add documentation for the new tool
4. Create tests for the new tool

## Documentation

Please update documentation when making changes:

- **README.md** for high-level changes
- **Code docstrings** for API changes
- **Comments** for complex logic

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

## Questions?

If you have questions about contributing, please open an issue or reach out to the maintainers. 