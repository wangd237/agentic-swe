"""Prepare a local codebase-memory-mcp release binary for evaluations."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlretrieve


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


DEFAULT_VERSION = "0.8.1"
DEFAULT_RELEASE_URL_TEMPLATE = (
    "https://github.com/DeusData/codebase-memory-mcp/releases/download/"
    "v{version}/codebase-memory-mcp-windows-amd64.zip"
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_version(binary_path: Path, timeout_sec: float = 10.0) -> dict:
    try:
        completed = subprocess.run(
            [str(binary_path), "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            check=False,
        )
        version_text = (completed.stdout or completed.stderr or "").strip().splitlines()
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "version": version_text[0] if version_text else "",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "error": "",
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "returncode": None,
            "version": "",
            "stdout": "",
            "stderr": "",
            "error": f"{exc.__class__.__name__}:{exc}",
        }


def prepare_codebase_memory_binary(
    *,
    output_dir: str | Path = ".tools/codebase-memory-mcp",
    version: str = DEFAULT_VERSION,
    release_url: str | None = None,
    download: bool = False,
    force: bool = False,
) -> dict:
    destination_dir = Path(output_dir).resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    binary_path = destination_dir / "codebase-memory-mcp.exe"
    archive_path = destination_dir / f"codebase-memory-mcp-windows-amd64-v{version}.zip"
    resolved_release_url = release_url or DEFAULT_RELEASE_URL_TEMPLATE.format(version=version)

    source = "existing" if binary_path.exists() else "missing"
    if force and binary_path.exists():
        binary_path.unlink()
        source = "removed_by_force"

    if not binary_path.exists() and download:
        urlretrieve(resolved_release_url, archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(destination_dir)
        source = "downloaded_release"

    path_binary = shutil.which("codebase-memory-mcp")
    if not binary_path.exists() and path_binary:
        binary_path = Path(path_binary).resolve()
        source = "path"

    version_record = _run_version(binary_path) if binary_path.exists() else {
        "ok": False,
        "returncode": None,
        "version": "",
        "stdout": "",
        "stderr": "",
        "error": "binary_not_found",
    }
    manifest = {
        "created_at": _utc_timestamp(),
        "requested_version": version,
        "release_url": resolved_release_url,
        "download_requested": download,
        "source": source,
        "binary_path": str(binary_path) if binary_path.exists() else "",
        "binary_exists": binary_path.exists(),
        "version_record": version_record,
    }
    manifest_path = destination_dir / "manifest.json"
    manifest_md_path = destination_dir / "manifest.md"
    write_json(manifest_path, manifest)
    write_text(manifest_md_path, build_markdown(manifest))
    return {
        "manifest_path": str(manifest_path),
        "manifest_md_path": str(manifest_md_path),
        "manifest": manifest,
    }


def build_markdown(manifest: dict) -> str:
    return f"""# Codebase Memory MCP Binary

- requested_version: `{manifest["requested_version"]}`
- binary_exists: `{manifest["binary_exists"]}`
- binary_path: `{manifest["binary_path"] or "N/A"}`
- source: `{manifest["source"]}`
- version: `{manifest["version_record"].get("version") or "N/A"}`
- error: `{manifest["version_record"].get("error") or "N/A"}`
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a local codebase-memory-mcp binary.")
    parser.add_argument("--output-dir", default=".tools/codebase-memory-mcp")
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--release-url", default="")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = prepare_codebase_memory_binary(
        output_dir=REPO_ROOT / args.output_dir,
        version=args.version,
        release_url=args.release_url or None,
        download=args.download,
        force=args.force,
    )
    manifest = output["manifest"]
    print("=== Codebase Memory MCP Binary ===")
    print(f"binary_exists: {manifest['binary_exists']}")
    print(f"binary_path: {manifest['binary_path'] or '(missing)'}")
    print(f"source: {manifest['source']}")
    print(f"version: {manifest['version_record'].get('version') or '(unknown)'}")
    print(f"manifest_path: {output['manifest_path']}")
    return 0 if manifest["binary_exists"] and manifest["version_record"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
