#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

echo "==> Running documentation validation checks"

python <<'PY'
from __future__ import annotations

import pathlib
import re
import sys
from typing import Dict, Iterable, List, Set, Tuple

ROOT = pathlib.Path.cwd()
SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".venv",
}
PYTHON_VALIDATE_DOCS = {
    pathlib.Path("README.md"),
    pathlib.Path("API.md"),
    pathlib.Path("DEVELOPMENT.md"),
    pathlib.Path("DEPLOYMENT.md"),
    pathlib.Path("USER_GUIDE.md"),
}
MarkdownFile = pathlib.Path
RouteKey = Tuple[str, str]

def _iter_markdown_files() -> Iterable[MarkdownFile]:
    for path in ROOT.rglob("*.md"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        yield path

def _check_internal_links() -> List[str]:
    errors: List[str] = []
    link_regex = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for md_path in _iter_markdown_files():
        text = md_path.read_text(encoding="utf-8")
        for match in link_regex.finditer(text):
            start = match.start()
            if start > 0 and text[start - 1] in {"!", "`"}:
                continue
            target = match.group(2).strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "tel:", "#")):
                continue
            if target.startswith("{"):
                # Skip templated links that will be resolved at render time
                continue
            target_path = target.split("#", 1)[0].split("?", 1)[0]
            if not target_path:
                continue
            resolved = (md_path.parent / target_path).resolve()
            if not str(resolved).startswith(str(ROOT)):
                continue
            if not resolved.exists():
                errors.append(f"{md_path}: broken link -> {target}")
    return errors

def _read_file(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")

def _check_changelog_format() -> List[str]:
    changelog_path = ROOT / "CHANGELOG.md"
    if not changelog_path.exists():
        return ["CHANGELOG.md is missing"]
    text = _read_file(changelog_path)
    errors: List[str] = []
    if "## [Unreleased]" not in text:
        errors.append("CHANGELOG.md must contain an 'Unreleased' section")
    release_pattern = re.compile(r"^## \[[^\]]+\] - \d{4}-\d{2}-[0-9A-Z]{2}$", re.MULTILINE)
    if not release_pattern.findall(text):
        errors.append(
            "CHANGELOG.md must contain at least one release heading with format '## [x.y.z] - YYYY-MM-DD'"
        )
    return errors

def _parse_api_prefix() -> str:
    config_path = ROOT / "backend" / "app" / "core" / "config.py"
    default_prefix = "/api/v1"
    if not config_path.exists():
        return default_prefix
    text = _read_file(config_path)
    match = re.search(r"api_v1_prefix:\s*str\s*=\s*Field\(default=\"([^\"]+)\"", text)
    if match:
        return match.group(1)
    return default_prefix

def _extract_module_prefixes(routes_text: str) -> Dict[str, str]:
    include_regex = re.compile(
        r"api_router\.include_router\(\s*([a-zA-Z0-9_]+)\.router(?:,\s*prefix=\s*\"([^\"]*)\")?"
    )
    prefixes: Dict[str, str] = {}
    for module_name, prefix in include_regex.findall(routes_text):
        prefixes[module_name] = prefix or ""
    return prefixes

def _extract_router_prefix(module_text: str) -> str:
    router_regex = re.compile(r"router\s*=\s*APIRouter\(([^)]*)\)")
    match = router_regex.search(module_text)
    if not match:
        return ""
    args = match.group(1)
    prefix_match = re.search(r"prefix\s*=\s*\"([^\"]*)\"", args)
    if not prefix_match:
        prefix_match = re.search(r"prefix\s*=\s*'([^']*)'", args)
    return prefix_match.group(1) if prefix_match else ""

def _compose_path(*segments: str) -> str:
    cleaned: List[str] = []
    for segment in segments:
        if not segment:
            continue
        fragment = segment.strip("/")
        if not fragment:
            continue
        cleaned.append(fragment)
    if not cleaned:
        return "/"
    return "/" + "/".join(cleaned)

def _normalise_for_docs(path: str, api_prefix: str) -> str:
    path = path or "/"
    api_prefix = api_prefix.rstrip("/")
    if api_prefix and path.startswith(api_prefix):
        relative = path[len(api_prefix):]
        if not relative:
            return "/"
        path = relative
    if not path.startswith("/"):
        path = "/" + path
    return path

def _extract_routes(module_text: str) -> List[Tuple[str, str]]:
    route_regex = re.compile(
        r"@router\.(get|post|put|patch|delete|options|head)\(\s*(['\"])([^'\"]*)\2",
        re.MULTILINE,
    )
    routes: List[Tuple[str, str]] = []
    for match in route_regex.finditer(module_text):
        method = match.group(1).upper()
        path = match.group(3)
        routes.append((method, path))
    return routes

def _collect_backend_routes() -> Set[RouteKey]:
    api_prefix = _parse_api_prefix()
    routes_py = ROOT / "backend" / "app" / "api" / "routes.py"
    if not routes_py.exists():
        return set()
    routes_text = _read_file(routes_py)
    module_prefixes = _extract_module_prefixes(routes_text)
    backend_dir = ROOT / "backend" / "app" / "api" / "endpoints"
    route_keys: Set[RouteKey] = set()

    # Include routes declared directly on router in routes.py (e.g. /health)
    direct_routes = _extract_routes(routes_text)
    for method, path in direct_routes:
        final_path = _compose_path(path)
        normalised = _normalise_for_docs(final_path, api_prefix)
        route_keys.add((method, normalised))

    for module_file in backend_dir.glob("*.py"):
        module_name = module_file.stem
        module_text = _read_file(module_file)
        router_prefix = _extract_router_prefix(module_text)
        include_prefix = module_prefixes.get(module_name, "")
        for method, path in _extract_routes(module_text):
            final_path = _compose_path(api_prefix, include_prefix, router_prefix, path)
            normalised = _normalise_for_docs(final_path, api_prefix)
            route_keys.add((method, normalised))
    return route_keys

def _collect_documented_routes() -> Set[RouteKey]:
    api_doc = ROOT / "API.md"
    if not api_doc.exists():
        return set()
    text = _read_file(api_doc)
    doc_pattern = re.compile(r"^###\s+\d+\.\s+([A-Z]+)\s+([^\s]+)\s*$", re.MULTILINE)
    documented: Set[RouteKey] = set()
    for method, path in doc_pattern.findall(text):
        cleaned_path = path if path.startswith("/") else f"/{path}"
        documented.add((method.upper(), cleaned_path))
    return documented

def _check_api_docs_alignment() -> List[str]:
    errors: List[str] = []
    backend_routes = _collect_backend_routes()
    documented_routes = _collect_documented_routes()
    missing_in_docs = sorted(backend_routes - documented_routes)
    if missing_in_docs:
        for method, path in missing_in_docs:
            errors.append(
                f"API.md is missing documentation for endpoint: {method} {path}"
            )
    undocumented_in_code = sorted(documented_routes - backend_routes)
    if undocumented_in_code:
        for method, path in undocumented_in_code:
            errors.append(
                f"API.md documents {method} {path} but no matching backend route was found"
            )
    return errors

def _check_code_examples() -> List[str]:
    errors: List[str] = []
    example_regex = re.compile(r"```python\n(.*?)```", re.DOTALL)
    for md_path in _iter_markdown_files():
        try:
            relative = md_path.relative_to(ROOT)
        except ValueError:
            continue
        if relative not in PYTHON_VALIDATE_DOCS:
            continue
        text = _read_file(md_path)
        for block in example_regex.findall(text):
            snippet = block.strip()
            if not snippet:
                continue
            try:
                compile(snippet, filename=str(md_path), mode="exec")
            except SyntaxError as exc:
                errors.append(
                    f"Python example in {relative} contains invalid syntax: line {exc.lineno}: {exc.msg}"
                )
    return errors

def main() -> None:
    checks = [
        ("Internal links", _check_internal_links),
        ("CHANGELOG format", _check_changelog_format),
        ("API documentation alignment", _check_api_docs_alignment),
        ("Python code examples", _check_code_examples),
    ]
    all_errors: List[str] = []
    for name, func in checks:
        print(f"- {name}...")
        errors = func()
        if errors:
            all_errors.extend(errors)
    if all_errors:
        print("\n❌ Documentation validation failed:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    print("\n✅ Documentation validation passed")

if __name__ == "__main__":
    main()
PY

PY_RESULT=$?
if [[ ${PY_RESULT} -ne 0 ]]; then
    exit ${PY_RESULT}
fi

echo "==> Documentation checks completed"
