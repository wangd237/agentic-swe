from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import prepare_codebase_memory_binary


def test_prepare_codebase_memory_binary_records_missing_without_download(tmp_path: Path) -> None:
    output = prepare_codebase_memory_binary.prepare_codebase_memory_binary(
        output_dir=tmp_path / "tools",
        version="0.8.1",
        download=False,
    )

    manifest = output["manifest"]
    assert manifest["binary_exists"] is False
    assert manifest["binary_path"] == ""
    assert manifest["version_record"]["error"] == "binary_not_found"
    assert "v0.8.1" in manifest["release_url"]
    assert Path(output["manifest_path"]).exists()
    assert Path(output["manifest_md_path"]).exists()


def test_build_markdown_includes_binary_status() -> None:
    markdown = prepare_codebase_memory_binary.build_markdown(
        {
            "requested_version": "0.8.1",
            "binary_exists": True,
            "binary_path": "C:/tools/codebase-memory-mcp.exe",
            "source": "downloaded_release",
            "version_record": {
                "version": "codebase-memory-mcp 0.8.1",
                "error": "",
            },
        }
    )

    assert "binary_exists" in markdown
    assert "codebase-memory-mcp 0.8.1" in markdown
