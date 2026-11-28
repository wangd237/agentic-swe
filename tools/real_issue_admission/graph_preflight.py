"""Exercise the real Linux graph backend offline before any paid task."""
import json
import pathlib
import subprocess
from admission import sha
from prepare_graph import VERSION, ASSETS

def validate_graph_dir(path):
    if set(x.name for x in path.iterdir()) != {"codebase-memory-mcp", "graph.lock.json"}:
        raise ValueError("Unexpected graph mount content")
    if any(x.is_symlink() for x in path.iterdir()):
        raise ValueError("Symlinks not allowed in graph mount")
    lock = json.loads((path/"graph.lock.json").read_text(encoding="utf-8"))
    if lock["version"] != VERSION or ASSETS.get(lock["architecture"]) != lock["archive_sha256"] or sha(path/"codebase-memory-mcp") != lock["binary_sha256"]:
        raise ValueError("Graph lock drift")
    return lock

def check_graph(runtime, source, app, graph, policy, issue_text):
    lock = validate_graph_dir(graph)
    image = runtime["image"]
    image_info = subprocess.check_output(["docker","image","inspect",image,"--format","{{.Id}} {{.Architecture}}"], text=True).strip().split()
    if image_info != [runtime["image_id"], lock["architecture"]]:
        raise ValueError("Image digest or graph architecture mismatch")
    code = """import json, subprocess, sys
from app.core.policy_config import load_policy_config
from app.codebase.intelligence import build_code_intelligence_backend
p = load_policy_config('/run/policy.json')
v = subprocess.check_output([p.codebase_memory_binary, '--version'], text=True, stderr=subprocess.STDOUT)
assert '0.8.1' in v, v
backend = build_code_intelligence_backend(p)
try:
    result = backend.collect_localization_hints(repo_path='/run/source', issue_text=sys.argv[1], max_results=p.code_intelligence_max_results)
    assert result.available and result.metrics.get('index_success') and backend.is_indexed(), result.to_dict()
    query = backend.search_graph_query(name_pattern='.*', max_results=1)
    assert query.get('ok'), query
    print(json.dumps(result.to_dict()))
finally:
    backend.cleanup()
"""
    cmd = ["docker","run","--rm","--network","none","--read-only","--tmpfs","/tmp",
           "--tmpfs","/run/.code_intelligence_shadow:exec","--cap-drop","ALL","--security-opt","no-new-privileges",
           "--pids-limit","256","-e","HOME=/tmp","-w","/run",
           "--mount",f"type=bind,source={source},target=/run/source,readonly",
           "--mount",f"type=bind,source={app},target=/run/app,readonly",
           "--mount",f"type=bind,source={graph},target=/opt/real_issue_graph,readonly",
           "--mount",f"type=bind,source={policy},target=/run/policy.json,readonly",
           image,runtime.get("agent_python","python"),"-c",code,issue_text]
    subprocess.run(cmd,check=True,timeout=600)
