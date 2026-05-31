"""Detect unused packages in requirements.txt by scanning imports."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

__all__ = ["check", "scan_imports", "read_requirements", "find_missing", "compare"]

# Common mapping of PyPI package names to import names where they differ
_PACKAGE_TO_IMPORT: dict[str, str] = {
    "pillow": "PIL",
    "scikit-learn": "sklearn",
    "python-dateutil": "dateutil",
    "pyyaml": "yaml",
    "beautifulsoup4": "bs4",
    "python-dotenv": "dotenv",
    "attrs": "attr",
    "opencv-python": "cv2",
    "pymysql": "pymysql",
    "psycopg2-binary": "psycopg2",
    "python-jose": "jose",
    "python-multipart": "multipart",
}

# Standard library module names (Python 3.10+) - top-level only
_STDLIB = frozenset({
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio",
    "asyncore", "atexit", "audioop", "base64", "bdb", "binascii",
    "binhex", "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb",
    "chunk", "cmath", "cmd", "code", "codecs", "codeop", "collections",
    "colorsys", "compileall", "concurrent", "configparser", "contextlib",
    "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal",
    "difflib", "dis", "distutils", "doctest", "email", "encodings",
    "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput",
    "fnmatch", "fractions", "ftplib", "functools", "gc", "getopt",
    "getpass", "gettext", "glob", "graphlib", "grp", "gzip", "hashlib",
    "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr",
    "imp", "importlib", "inspect", "io", "ipaddress", "itertools",
    "json", "keyword", "lib2to3", "linecache", "locale", "logging",
    "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
    "mmap", "modulefinder", "msvcrt", "multiprocessing", "netrc",
    "nis", "nntplib", "numbers", "operator", "optparse", "os",
    "ossaudiodev", "pathlib", "pdb", "pickle", "pickletools", "pipes",
    "pkgutil", "platform", "plistlib", "poplib", "posix", "posixpath",
    "pprint", "profile", "pstats", "pty", "pwd", "py_compile",
    "pyclbr", "pydoc", "queue", "quopri", "random", "re", "readline",
    "reprlib", "resource", "rlcompleter", "runpy", "sched", "secrets",
    "select", "selectors", "shelve", "shlex", "shutil", "signal",
    "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver",
    "spwd", "sqlite3", "sre_compile", "sre_constants", "sre_parse",
    "ssl", "stat", "statistics", "string", "stringprep", "struct",
    "subprocess", "sunau", "symtable", "sys", "sysconfig", "syslog",
    "tabnanny", "tarfile", "telnetlib", "tempfile", "termios", "test",
    "textwrap", "threading", "time", "timeit", "tkinter", "token",
    "tokenize", "tomllib", "trace", "traceback", "tracemalloc",
    "tty", "turtle", "turtledemo", "types", "typing", "unicodedata",
    "unittest", "urllib", "uu", "uuid", "venv", "warnings", "wave",
    "weakref", "webbrowser", "winreg", "winsound", "wsgiref",
    "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport",
    "zlib", "_thread", "__future__",
})


def scan_imports(path: str | Path) -> set[str]:
    """Scan Python files for top-level import names.

    Args:
        path: Directory or file to scan.

    Returns:
        Set of top-level module names that are imported.
    """
    root = Path(path)
    imports: set[str] = set()

    files = root.rglob("*.py") if root.is_dir() else [root]

    for file in files:
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    imports.add(node.module.split(".")[0])

    return imports


def read_requirements(path: str | Path) -> list[str]:
    """Read package names from requirements.txt.

    Args:
        path: Path to requirements.txt file.

    Returns:
        List of package names (lowercase, without version specifiers).
    """
    reqs: list[str] = []
    text = Path(path).read_text(encoding="utf-8")

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Remove version specifiers
        for sep in (">=", "<=", "==", "!=", "~=", ">", "<", "["):
            line = line.split(sep)[0]
        name = line.strip().lower()
        if name:
            reqs.append(name)

    return reqs


def _read_pyproject_deps(path: str | Path) -> list[str]:
    """Read dependencies from pyproject.toml."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return []

    text = Path(path).read_text(encoding="utf-8")
    data = tomllib.loads(text)
    deps = data.get("project", {}).get("dependencies", [])

    result: list[str] = []
    for dep in deps:
        for sep in (">=", "<=", "==", "!=", "~=", ">", "<", "[", " "):
            dep = dep.split(sep)[0]
        name = dep.strip().lower()
        if name:
            result.append(name)

    return result


def _import_name_for_package(package: str) -> str:
    """Get the import name for a PyPI package."""
    lower = package.lower()
    if lower in _PACKAGE_TO_IMPORT:
        return _PACKAGE_TO_IMPORT[lower]
    return lower.replace("-", "_")


def check(
    path: str | Path,
    *,
    requirements: str | Path | None = None,
) -> list[str]:
    """Find unused packages by comparing imports against requirements.

    Args:
        path: Directory to scan for Python imports.
        requirements: Path to requirements.txt. Auto-detected if not specified.

    Returns:
        List of package names that appear in requirements but not in imports.
    """
    root = Path(path)
    imports = scan_imports(root)
    import_names_lower = {name.lower() for name in imports}

    # Find requirements
    packages: list[str] = []
    if requirements:
        packages = read_requirements(requirements)
    else:
        req_path = root / "requirements.txt"
        if req_path.exists():
            packages = read_requirements(req_path)

        pyproject_path = root / "pyproject.toml"
        if pyproject_path.exists():
            packages.extend(_read_pyproject_deps(pyproject_path))

    # Compare
    unused: list[str] = []
    for pkg in packages:
        import_name = _import_name_for_package(pkg).lower()
        if import_name not in import_names_lower:
            unused.append(pkg)

    return unused


def find_missing(
    requirements_path: str | Path,
    source_dir: str | Path,
) -> set[str]:
    """Return imports used in *source_dir* but NOT declared in *requirements_path*.

    Inverse of check(), which finds unused packages. Stdlib imports are
    excluded. Package name normalization (PyPI <-> import name) is applied
    so e.g. 'pyyaml' in requirements satisfies 'import yaml' in source.

    Args:
        requirements_path: Path to requirements.txt file.
        source_dir: Directory (or file) to scan for Python imports.

    Returns:
        Set of top-level import names used in source but not declared.
    """
    used_imports = scan_imports(source_dir)
    used_imports = {name for name in used_imports if name not in _STDLIB}

    declared_packages = read_requirements(requirements_path)
    declared_imports = {_import_name_for_package(pkg) for pkg in declared_packages}

    return used_imports - declared_imports


def compare(
    req_a: str | Path,
    req_b: str | Path,
) -> dict[str, list[str]]:
    """Diff two requirements files by package name.

    Args:
        req_a: Path to the first requirements file.
        req_b: Path to the second requirements file.

    Returns:
        Dict with keys "added" (in b but not a), "removed" (in a but not b),
        and "common" (in both). Each value is a sorted list of package names.
    """
    set_a = set(read_requirements(req_a))
    set_b = set(read_requirements(req_b))

    return {
        "added": sorted(set_b - set_a),
        "removed": sorted(set_a - set_b),
        "common": sorted(set_a & set_b),
    }
