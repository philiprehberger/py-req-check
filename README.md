# philiprehberger-req-check

[![Tests](https://github.com/philiprehberger/py-req-check/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-req-check/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-req-check.svg)](https://pypi.org/project/philiprehberger-req-check/)
[![License](https://img.shields.io/github/license/philiprehberger/py-req-check)](LICENSE)

Detect unused packages in requirements.txt by scanning imports.

## Install

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

## License

MIT
