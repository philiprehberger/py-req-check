# philiprehberger-req-check

[![Tests](https://github.com/philiprehberger/py-req-check/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-req-check/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-req-check.svg)](https://pypi.org/project/philiprehberger-req-check/)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-req-check)](https://github.com/philiprehberger/py-req-check/commits/main)

Detect unused packages in requirements.txt by scanning imports.

## Installation

```bash
pip install philiprehberger-req-check
```

## Usage

```python
from philiprehberger_req_check import check

# Find unused packages in a project directory
unused = check("./my-project")
print(unused)  # ["some-unused-package"]
```

### Scan Imports

```python
from philiprehberger_req_check import scan_imports

imports = scan_imports("./my-project")
print(imports)  # {"requests", "flask", "os", "sys", ...}
```

### Read Requirements

```python
from philiprehberger_req_check import read_requirements

packages = read_requirements("requirements.txt")
print(packages)  # ["requests", "flask", "pillow"]
```

### CLI

```bash
python -m philiprehberger_req_check ./my-project
```

Exits with code 1 if unused packages are found.

## API

| Function | Description |
|----------|-------------|
| `check(path, *, requirements=None)` | Find unused packages by comparing imports against requirements |
| `scan_imports(path)` | Scan Python files for top-level import names |
| `read_requirements(path)` | Read package names from requirements.txt |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Support

If you find this project useful:

⭐ [Star the repo](https://github.com/philiprehberger/py-req-check)

🐛 [Report issues](https://github.com/philiprehberger/py-req-check/issues?q=is%3Aissue+is%3Aopen+label%3Abug)

💡 [Suggest features](https://github.com/philiprehberger/py-req-check/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)

❤️ [Sponsor development](https://github.com/sponsors/philiprehberger)

🌐 [All Open Source Projects](https://philiprehberger.com/open-source-packages)

💻 [GitHub Profile](https://github.com/philiprehberger)

🔗 [LinkedIn Profile](https://www.linkedin.com/in/philiprehberger)

## License

[MIT](LICENSE)
