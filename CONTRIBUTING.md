# Contributing to cc2oc-bridge

Thank you for your interest in contributing to cc2oc-bridge! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- OpenCode installed (for testing)
- A GitHub account

### Finding Issues to Work On

Look for issues labeled:
- `good first issue` - Perfect for newcomers
- `help wanted` - Needs community contribution
- `bug` - Bug fixes needed
- `enhancement` - New features to implement

## How to Contribute

### 1. Reporting Bugs

If you find a bug, please create an issue with:

**Title**: Clear, descriptive title
**Labels**: Add `bug` label
**Description**:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your environment (OS, Python version, OpenCode version)
- Screenshots or logs if applicable

Use our [bug report template](https://github.com/Code-Glider/cc2oc-bridge/issues/new?template=bug_report.md).

### 2. Suggesting Features

For feature requests, create an issue with:

**Title**: Descriptive feature name
**Labels**: Add `enhancement` label
**Description**:
- Clear description of the feature
- Why this feature would be useful
- Any implementation ideas you have
- Examples of how it would work

Use our [feature request template](https://github.com/Code-Glider/cc2oc-bridge/issues/new?template=feature_request.md).

### 3. Contributing Code

#### Small Changes (Fixes, Typos)

For small changes like:
- Fixing typos in documentation
- Minor bug fixes
- Code style improvements

You can:
1. Fork the repository
2. Make your changes
3. Submit a pull request

#### Large Changes (Features, Refactoring)

For larger changes:
1. **Discuss First**: Open an issue to discuss your idea
2. **Get Approval**: Wait for maintainer approval before starting
3. **Follow Process**: Use the full development workflow below

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub first
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/cc2oc-bridge.git
cd cc2oc-bridge

# Add upstream remote
git remote add upstream https://github.com/Code-Glider/cc2oc-bridge.git
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt  # If we create one
pip install pyyaml  # Main dependency
```

### 3. Install Development Tools

```bash
# Install development dependencies
pip install pytest flake8 black mypy

# Or if we have a requirements-dev.txt
pip install -r requirements-dev.txt
```

### 4. Verify Setup

```bash
# Test the installation
python3 loader.py --list
python3 hooks.py
```

## Development Workflow

### 1. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch Naming Conventions**:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions

### 2. Make Your Changes

- Write clean, readable code
- Add comments for complex logic
- Follow our coding standards (see below)
- Update documentation as needed
- Add tests for new functionality

### 3. Test Your Changes

```bash
# Run existing tests
python3 -m pytest tests/ -v

# Test manually
python3 loader.py --list
python3 hooks.py

# Test with OpenCode if possible
# @cc2oc-bridge load
# @cc2oc-bridge run test-plugin:greet
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a clear message
git commit -m "Add: brief description of your changes"

# Or commit specific files
git add file1.py file2.py
git commit -m "Fix: resolve issue with X"
```

**Commit Message Format**:

```
Type: Brief description (50 chars max)

Detailed explanation if needed. Wrap at 72 characters.
Reference issues with #123.

Types:
- Add: New feature
- Fix: Bug fix
- Docs: Documentation changes
- Style: Code style changes
- Refactor: Code refactoring
- Test: Test additions/changes
- Chore: Maintenance tasks
```

**Examples**:

```
Add: support for YAML-style tool lists

Implements parsing of both string and list formats for
allowed-tools in command frontmatter. Fixes #45.
```

```
Fix: resolve path rewriting for nested directories

The path rewriter now correctly handles nested directory
structures when installing plugins. Resolves #78.
```

### 5. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a pull request on GitHub
```

## Pull Request Process

### Before Submitting

- [ ] Code follows our style guidelines
- [ ] Self-review completed
- [ ] Code is commented where needed
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Commit messages are clear

### Pull Request Template

When creating a PR, include:

**Title**: `Type: Brief description`

**Description**:
- What changes you made
- Why you made them
- Any issues it resolves (use `Fixes #123`)
- Screenshots if applicable

**Checklist**:
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Ready for merge

### Review Process

1. **Automated Checks**: CI/CD will run tests
2. **Code Review**: Maintainers will review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged

## Coding Standards

### Python Code Style

- Follow **PEP 8** guidelines
- Use **Black** for code formatting
- Maximum line length: 88 characters
- Use type hints where appropriate
- Write docstrings for public functions

```bash
# Format your code
black .

# Check for style issues
flake8 .

# Type checking
mypy .
```

### Documentation Style

- Use clear, concise language
- Include examples where helpful
- Update README.md for user-facing changes
- Update AGENTS.md for architecture changes
- Use Markdown for documentation

### Testing Standards

- Write tests for new functionality
- Maintain or improve code coverage
- Use descriptive test names
- Test both success and failure cases

```python
# Example test structure
def test_loader_discover_commands():
    """Test that loader discovers commands correctly."""
    # Arrange
    loader = ComponentLoader()
    
    # Act
    commands = loader.discover_commands("plugins/test-plugin")
    
    # Assert
    assert "greet" in commands
    assert len(commands) > 0
```

## Documentation

### Updating Documentation

When you make changes:

1. **Code Changes**: Update docstrings and comments
2. **User-Facing Changes**: Update README.md
3. **Architecture Changes**: Update AGENTS.md
4. **New Features**: Add examples to examples/
5. **API Changes**: Update docs/DIRECTIVE.md

### Documentation Files

- `README.md` - Main project documentation
- `AGENTS.md` - Architecture and technical details
- `docs/DIRECTIVE.md` - Directive documentation
- `docs/TEST_PLAN.md` - Testing strategies
- `examples/` - Example commands and agents
- `USER_MANUAL.md` - User guide

## Testing

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_loader.py -v

# Run with coverage
python3 -m pytest tests/ --cov=cc2oc_bridge --cov-report=html
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use pytest framework
- Mock external dependencies
- Test edge cases

### Manual Testing

Test with the included test plugin:

```bash
# Install test plugin
./install-plugin.sh plugins/test-plugin test-plugin

# Test commands
@cc2oc-bridge run test-plugin:greet
@cc2oc-bridge run test-plugin:count-files md

# Test agents
@cc2oc-bridge agent test-plugin:helper "List files"

# Test hooks
python3 hooks.py
```

## Reporting Issues

### Bug Reports

Include as much detail as possible:

1. **Environment**: OS, Python version, OpenCode version
2. **Steps to Reproduce**: Numbered steps
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Error Messages**: Full error text
6. **Screenshots**: If applicable
7. **Logs**: Relevant log output

### Security Issues

**DO NOT** report security issues publicly. Instead:

1. Email security@cc2oc-bridge.dev
2. Include detailed description
3. Allow time for investigation before disclosure

## Feature Requests

We welcome feature requests! To increase chances of acceptance:

1. **Explain the Use Case**: Why is this feature needed?
2. **Describe the Solution**: How should it work?
3. **Consider Alternatives**: Are there other ways to achieve this?
4. **Mockups/Examples**: Show what it would look like

## Recognition

Contributors will be:

- Listed in README.md contributors section
- Mentioned in release notes
- Given credit in commit messages
- Invited to join discussions about project direction

## Questions?

If you're unsure about anything:

1. Check existing issues and PRs
2. Read the documentation thoroughly
3. Ask in [Discussions](https://github.com/Code-Glider/cc2oc-bridge/discussions)
4. Tag maintainers in issues if needed

## Thank You!

Your contributions make cc2oc-bridge better for everyone. We appreciate:

- Your time and effort
- Your expertise and insights
- Your patience with the review process
- Your commitment to quality

Happy coding! 🚀

---

**Maintainers**: @Code-Glider and contributors

**Last Updated**: 2024-01-11