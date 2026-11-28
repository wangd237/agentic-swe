"""Download and verify the original graph tool's Linux release; no LLM calls."""
import argparse
import hashlib
import json
import pathlib
import tarfile
import tempfile
import urllib.request

VERSION = "0.8.1"
ASSETS = {
    "amd64": "dbd3b92ea870ef240b63059f26bda15015f76ef9978931bebc3a0f9d09470973",
    "arm64": "d2f842d1365da5c35d9c5796f57a821c9745267350994346735e1e6e04d46091",
}
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare(target, arch):
    if target.exists():
        raise FileExistsError(target)
    name = f"codebase-memory-mcp-linux-{arch}.tar.gz"
    url = f"https://github.com/DeusData/codebase-memory-mcp/releases/download/v{VERSION}/{name}"
    with tempfile.TemporaryDirectory() as tmp:
        archive = pathlib.Path(tmp)/name
        urllib.request.urlretrieve(url, archive)
        if sha(archive) != ASSETS[arch]:
            raise ValueError("Release archive digest mismatch")
        with tarfile.open(archive) as tar:
            members = [m for m in tar.getmembers() if m.isfile() and pathlib.PurePosixPath(m.name).name == "codebase-memory-mcp"]
            if len(members) != 1:
                raise ValueError("Expected exactly one binary in official archive")
            data = tar.extractfile(members[0]).read()
        target.mkdir(parents=True)
        binary = target/"codebase-memory-mcp"
        binary.write_bytes(data)
        binary.chmod(0o755)
        (target/"graph.lock.json").write_text(json.dumps({"version": VERSION, "architecture": arch, "archive_sha256": ASSETS[arch], "binary_sha256": sha(binary)}, indent=2), encoding="utf-8")
    return target

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("target", type=pathlib.Path)
    p.add_argument("--arch", choices=ASSETS, default="amd64")
    a = p.parse_args()
    print(prepare(a.target.resolve(), a.arch))
