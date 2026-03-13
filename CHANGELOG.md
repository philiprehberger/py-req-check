# Changelog

## 0.1.0 (2026-03-13)

- Initial release
- `check()` to detect unused packages
- `scan_imports()` to extract imports from Python files
- `read_requirements()` to parse requirements.txt
- Auto-detects requirements.txt and pyproject.toml
- Common PyPI-to-import name mappings (pillow->PIL, etc.)
- CLI: `python -m philiprehberger_req_check [path]`
