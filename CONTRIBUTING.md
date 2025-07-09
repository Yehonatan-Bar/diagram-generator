# Contributing to AI Diagram Generator

First off, thank you for considering contributing to the AI Diagram Generator! It's people like you that make this tool better for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title** for the issue to identify the problem
* **Describe the exact steps which reproduce the problem** in as many details as possible
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior
* **Explain which behavior you expected to see instead and why**
* **Include logs** if possible (with sensitive information redacted)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title** for the issue to identify the suggestion
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible
* **Provide specific examples to demonstrate the steps** or provide code snippets
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why
* **Explain why this enhancement would be useful** to most users

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Include screenshots and animated GIFs in your pull request whenever possible
* Follow the Python style guide (PEP 8)
* Include thoughtfully-worded, well-structured tests
* Document new code
* End all files with a newline

## Development Process

### Setting Up Your Development Environment

1. Fork the repo and create your branch from `main`:
   ```bash
   git clone https://github.com/yourusername/diagram-generator.git
   cd diagram-generator
   git checkout -b feature/your-feature-name
   ```

2. Set up the virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install development dependencies:
   ```bash
   pip install pytest pytest-asyncio pytest-cov black isort mypy
   ```

### Making Changes

1. Make your changes in a new git branch
2. Add or update tests as needed
3. Ensure the test suite passes:
   ```bash
   pytest
   ```

4. Format your code:
   ```bash
   black src tests
   isort src tests
   ```

5. Run type checking:
   ```bash
   mypy src
   ```

### Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

Example:
```
Add support for Azure cloud components

- Import Azure components from diagrams package
- Update NODE_TYPES mapping in diagram_builder.py
- Add Azure examples to documentation
- Update tests to cover new components

Fixes #123
```

### Testing

* Write tests for any new functionality
* Ensure all tests pass before submitting PR
* Aim for high test coverage (>80%)
* Test files should be in `tests/` mirroring the `src/` structure

Example test:
```python
import pytest
from src.agents.diagram_agent import DiagramAgent

@pytest.mark.asyncio
async def test_diagram_generation():
    agent = DiagramAgent(use_mock=True)
    result = await agent.generate_diagram("Create a simple web app")
    
    assert result["success"] is True
    assert "diagram_path" in result
    assert result["nodes_created"] > 0
```

### Documentation

* Update the README.md if needed
* Add docstrings to all public functions and classes
* Update API documentation for new endpoints
* Include examples for new features

### Style Guide

#### Python Style

* Follow PEP 8
* Use type hints for function parameters and returns
* Maximum line length: 100 characters
* Use descriptive variable names
* Prefer f-strings over .format() or %

#### Logging

Always use the dual-tag logging system:

```python
from src.core.logging import logger, FeatureTag, ModuleTag

logger.info(
    "Processing diagram request",
    feature=FeatureTag.API,
    module=ModuleTag.API_ENDPOINTS,
    request_id=request_id,
    description=description[:50]
)
```

#### Error Handling

Use proper error handling with meaningful messages:

```python
try:
    result = await generate_diagram(description)
except ValidationError as e:
    logger.error(
        "Validation failed",
        feature=FeatureTag.TOOLS,
        module=ModuleTag.TOOL_VALIDATOR,
        error=str(e)
    )
    raise HTTPException(status_code=400, detail=str(e))
```

## Project Structure

When adding new features, follow the existing structure:

* `src/api/` - API endpoints and models
* `src/agents/` - Agent implementations
* `src/tools/` - Tools and utilities
* `src/llm/` - LLM integrations
* `src/core/` - Core functionality (config, logging)
* `src/utils/` - Helper functions and decorators

## Questions?

Feel free to open an issue with the tag "question" if you have any questions about contributing.

Thank you for contributing! 🎉