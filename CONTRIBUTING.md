# Contributing to HEIC Converter Pro

First off, thank you for considering contributing to HEIC Converter Pro! It's people like you that make this tool better for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our commitment to providing a welcoming and inspiring community for all. Please be respectful and constructive in your communications.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps to reproduce the problem**
* **Provide specific examples** (sample files if possible)
* **Describe the behavior you observed and what you expected**
* **Include screenshots** if applicable
* **Include your environment details** (OS, Python version, dependency versions)
* **Attach the log file** (`heic_converter.log`) if relevant

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

* **Use a clear and descriptive title**
* **Provide a detailed description** of the suggested enhancement
* **Explain why this enhancement would be useful**
* **List any alternative solutions** you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the coding style** of the project
3. **Add tests** if you're adding new functionality
4. **Update documentation** if you're changing functionality
5. **Ensure the test suite passes**
6. **Write a clear commit message**

## Development Setup

### Prerequisites

* Python 3.7+
* Git
* Virtual environment tool (venv, virtualenv, or conda)

### Setup Steps

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Heic2Png.git
   cd Heic2Png
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Coding Standards

### Python Style Guide

* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
* Use type hints where appropriate
* Write docstrings for all functions, classes, and modules
* Keep functions focused and single-purpose
* Maximum line length: 100 characters

### Documentation

* Update the README.md if you change functionality
* Add docstrings to new functions/classes following the existing format
* Comment complex logic
* Keep comments up-to-date with code changes

### Commit Messages

* Use present tense ("Add feature" not "Added feature")
* Use imperative mood ("Move cursor to..." not "Moves cursor to...")
* Start with a capital letter
* Keep the first line under 72 characters
* Reference issues and pull requests when applicable

Example:
```
Add support for TIFF output format

- Implement TIFF conversion in convert_heic_to_png()
- Add TIFF to SUPPORTED_OUTPUT_FORMATS
- Update GUI to include TIFF option

Closes #123
```

## Testing

### Before Submitting

* Test your changes with various HEIC files
* Test with different output formats
* Test error handling (invalid files, missing directories, etc.)
* Verify thread safety with high thread counts
* Check memory usage with large batches

### Test Checklist

- [ ] Code runs without errors
- [ ] All existing features still work
- [ ] New features work as expected
- [ ] Error cases are handled gracefully
- [ ] Log messages are appropriate and helpful
- [ ] GUI remains responsive during conversions
- [ ] Configuration saves and loads correctly

## Project Structure

```
Heic2Png/
├── converter.py          # Main application code
├── requirements.txt      # Python dependencies
├── config.json          # User configuration (auto-generated)
├── README.md            # Project documentation
├── CONTRIBUTING.md      # This file
├── LICENSE              # MIT License
├── .gitignore          # Git ignore rules
├── input/              # Default input directory
└── output/             # Default output directory
```

## Areas for Contribution

We're particularly interested in contributions in these areas:

* **Performance Optimization**: Improving conversion speed
* **Format Support**: Adding new output formats (TIFF, GIF, etc.)
* **CLI Mode**: Command-line interface implementation
* **Metadata Handling**: Preserving EXIF data
* **UI Improvements**: Dark mode, localization, better themes
* **Testing**: Unit tests, integration tests
* **Documentation**: Tutorials, examples, translations
* **Bug Fixes**: Always appreciated!

## Questions?

Feel free to open an issue with your question or contact the maintainers.

## Recognition

Contributors will be recognized in:
* The project README.md
* Release notes for their contributions
* The project's GitHub contributors page

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to HEIC Converter Pro! 🎉
