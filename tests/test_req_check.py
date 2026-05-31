"""Tests for philiprehberger_req_check."""

from __future__ import annotations

import pytest
from pathlib import Path

from philiprehberger_req_check import (
    check,
    compare,
    find_missing,
    read_requirements,
    scan_imports,
)


def test_scan_imports_finds_import_statement(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("import requests\n", encoding="utf-8")
    result = scan_imports(tmp_path)
    assert "requests" in result


def test_scan_imports_finds_from_import(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "from bs4 import BeautifulSoup\n", encoding="utf-8"
    )
    result = scan_imports(tmp_path)
    assert "bs4" in result


def test_scan_imports_includes_stdlib(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "import os\nimport sys\nimport json\n", encoding="utf-8"
    )
    result = scan_imports(tmp_path)
    assert "os" in result
    assert "sys" in result
    assert "json" in result


def test_scan_imports_handles_syntax_errors(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("def foo(\n", encoding="utf-8")
    result = scan_imports(tmp_path)
    assert result == set()


def test_scan_imports_dotted_import(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("import os.path\n", encoding="utf-8")
    result = scan_imports(tmp_path)
    assert "os" in result
    assert "os.path" not in result


def test_scan_imports_single_file(tmp_path: Path) -> None:
    f = tmp_path / "script.py"
    f.write_text("import flask\n", encoding="utf-8")
    result = scan_imports(f)
    assert "flask" in result


def test_read_requirements_parses_names(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("requests\nflask\n", encoding="utf-8")
    result = read_requirements(req)
    assert result == ["requests", "flask"]


def test_read_requirements_strips_versions(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("requests>=2.28\nflask==2.3.0\nnumpy~=1.24\n", encoding="utf-8")
    result = read_requirements(req)
    assert result == ["requests", "flask", "numpy"]


def test_read_requirements_ignores_comments_and_blanks(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("# comment\n\nrequests\n\n# another\nflask\n", encoding="utf-8")
    result = read_requirements(req)
    assert result == ["requests", "flask"]


def test_read_requirements_handles_extras(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("uvicorn[standard]>=0.20\n", encoding="utf-8")
    result = read_requirements(req)
    assert result == ["uvicorn"]


def test_check_finds_unused_package(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("import flask\n", encoding="utf-8")
    req = tmp_path / "requirements.txt"
    req.write_text("flask\nrequests\n", encoding="utf-8")
    result = check(tmp_path)
    assert "requests" in result
    assert "flask" not in result


def test_check_returns_empty_when_all_used(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "import flask\nimport requests\n", encoding="utf-8"
    )
    req = tmp_path / "requirements.txt"
    req.write_text("flask\nrequests\n", encoding="utf-8")
    result = check(tmp_path)
    assert result == []


def test_check_handles_aliased_packages(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("from PIL import Image\n", encoding="utf-8")
    req = tmp_path / "requirements.txt"
    req.write_text("pillow\n", encoding="utf-8")
    result = check(tmp_path)
    assert result == []


def test_check_reads_pyproject_deps(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("import flask\n", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\ndependencies = ["flask>=2.0", "requests>=2.28"]\n',
        encoding="utf-8",
    )
    result = check(tmp_path)
    assert "requests" in result
    assert "flask" not in result


def test_check_with_explicit_requirements_path(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("import flask\n", encoding="utf-8")
    req = tmp_path / "reqs.txt"
    req.write_text("flask\nrequests\n", encoding="utf-8")
    result = check(src, requirements=req)
    assert "requests" in result
    assert "flask" not in result


def test_find_missing_returns_undeclared_imports(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text(
        "import yaml\nimport os\n", encoding="utf-8"
    )
    req = tmp_path / "requirements.txt"
    req.write_text("requests\n", encoding="utf-8")
    result = find_missing(req, src)
    assert result == {"yaml"}


def test_find_missing_resolves_pypi_to_import_name(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("import yaml\n", encoding="utf-8")
    req = tmp_path / "requirements.txt"
    req.write_text("pyyaml\n", encoding="utf-8")
    result = find_missing(req, src)
    assert result == set()


def test_find_missing_empty_source_dir(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    req = tmp_path / "requirements.txt"
    req.write_text("requests\n", encoding="utf-8")
    result = find_missing(req, src)
    assert result == set()


def test_compare_diffs_two_requirements_files(tmp_path: Path) -> None:
    req_a = tmp_path / "req_a.txt"
    req_a.write_text("requests\nyaml\n", encoding="utf-8")
    req_b = tmp_path / "req_b.txt"
    req_b.write_text("requests\nhttpx\n", encoding="utf-8")
    result = compare(req_a, req_b)
    assert result == {
        "added": ["httpx"],
        "removed": ["yaml"],
        "common": ["requests"],
    }


def test_compare_same_file(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("requests\nflask\nnumpy\n", encoding="utf-8")
    result = compare(req, req)
    assert result == {
        "added": [],
        "removed": [],
        "common": ["flask", "numpy", "requests"],
    }
