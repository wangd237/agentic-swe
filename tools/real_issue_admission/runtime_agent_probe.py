"""Run the existing Agent entry in one locked task container."""
import argparse
import json
import pathlib
import subprocess
import time

from admission import dump, sha
from score import score, CandidateRejected

P = pathlib.Path


def run(task_dir, agent_export, app_dir, image, label, llm_env=None, network='none', policy=None, expected_model=None, public_task=None, graph_dir=None):
    started = time.monotonic()
    if policy is not None and (llm_env is None or not expected_model):
        raise ValueError('Formal policy requires LLM env and expected model')
    if policy is not None and (network == 'none' or subprocess.check_output(['docker','network','inspect',network,'--format','{{.Internal}}'],text=True).strip() != 'true'):
        raise ValueError('Formal LLM network must be internal')
    if llm_env is None and network != 'none':
        raise ValueError('Non-LLM probe must be offline')
    if not label or label in {'.', '..'} or not all(c.isalnum() or c in '-_.' for c in label):
        raise ValueError('Invalid run label')
    graph_enabled = policy is not None and policy.get('code_intelligence_backend') == 'codebase_memory_cli'
    if graph_enabled and graph_dir is None:
        raise ValueError('Graph-enabled policy requires prepared Linux graph directory')
    if graph_enabled:
        from graph_preflight import validate_graph_dir
        validate_graph_dir(graph_dir)
    cfg = json.loads((task_dir/'review.json').read_text(encoding='utf-8'))
    prep = json.loads((task_dir/'prepared.json').read_text(encoding='utf-8'))
    runtime = json.loads((task_dir/'agent_runtime.json').read_text(encoding='utf-8'))
    if image != runtime['image']:
        raise ValueError('Agent image differs from runtime lock')
    image_id = subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],
                                       text=True).strip()
    if image_id != runtime['image_id']:
        raise ValueError('Agent image digest drift')
    agent_python = runtime.get('agent_python', 'python')
    freeze = subprocess.check_output(['docker','run','--rm','--network','none',image,
                                      agent_python,'-m','pip','freeze','--all'],text=True)
    lock = (task_dir/'agent_dependencies.lock.txt').read_text(encoding='utf-8')
    if freeze.replace('\r\n','\n') != lock.replace('\r\n','\n'):
        raise ValueError('Agent dependency lock drift')
    if not agent_export.is_dir() or list(agent_export.rglob('.git')):
        raise ValueError('invalid single-task Agent export')
    if public_task is not None:
        for key, expected in {'task_id': 'real_full_'+prep['task_id'].removeprefix('real_'),
                              'issue_title': cfg['issue_title'], 'issue_text': cfg['issue_text'],
                              'success_criteria': cfg['public_success_criteria'],
                              'difficulty': prep['difficulty']}.items():
            if public_task.get(key) != expected:
                raise ValueError('Frozen task differs from private review: '+key)
    out = task_dir/'runtime_agent_probe'/label
    if out.exists():
        raise FileExistsError(out)
    logs = out/'agent_logs'
    logs.mkdir(parents=True)
    task_id = public_task['task_id'] if public_task is not None else 'probe_'+prep['task_id']
    command = cfg['public_test_command']
    if prep['repo_full_name'] == 'agronholm/anyio':
        command = command.replace('python -m pytest', 'python -m pytest -p anyio.pytest_plugin', 1)
    if prep['repo_full_name'] == 'pydantic/pydantic':
        command = command.replace('python -m pytest', '/usr/local/bin/python -m pytest -o addopts=', 1)
    if public_task is not None and public_task['test_command'] not in (cfg['public_test_command'], command):
        raise ValueError('Frozen public test command drift')
    task = {
        'task_id': task_id,
        'repo_name': prep['repo_full_name'].split('/')[-1],
        'repo_path': 'source',
        'issue_title': cfg['issue_title'],
        'issue_text': cfg['issue_text'],
        'test_command': command,
        'success_criteria': cfg['public_success_criteria'],
        'difficulty': prep['difficulty'],
        'tags': ['bugfix', 'python', 'real-issue'],
        'target_files_hint': [],
        'expected_failure_test': cfg.get('visible_failure_test'),
        'max_retries': 2,
        'source_type': 'real_issue',
        'metadata': {},
    }
    dump(out/'task.json', task)
    if llm_env is not None:
        if network == 'none':
            raise ValueError('LLM acceptance requires the restricted model network')
        dump(out/'policy.json', policy if policy is not None else {
            'policy_id': 'real_issue_single_acceptance',
            'description': 'Single paid LLM runtime acceptance',
            'agent_type': 'llm', 'max_steps': 8,
            'llm_max_output_tokens': 4096,
            'llm_compaction_mode': 'rules',
            'llm_timeout_sec': 120,
            'llm_client_max_retries': 1,
        })
    code = '''import json, os
from app.core.policy_config import load_policy_config
from app.llm.config import LLMConfig
from app.runtime import task_runner
from app.agent import llm_agent
from app.runtime.agent_entry import run_agent

original = task_runner.copy_repo_to_workspace
def locked_copy(*args, **kwargs):
    return original(*args, install_editable=False, **kwargs)
task_runner.copy_repo_to_workspace = locked_copy
llm_agent.copy_repo_to_workspace = locked_copy
if os.environ.get('REAL_ISSUE_EXPECTED_MODEL'):
    p = load_policy_config('/run/policy.json')
    c = LLMConfig.from_policy(p)
    if p.agent_type != 'llm' or c.model != os.environ['REAL_ISSUE_EXPECTED_MODEL']:
        raise ValueError('Model or agent type drift')
    if c.context_window_tokens != p.llm_context_window_tokens:
        raise ValueError('Context window drift')
    print('EFFECTIVE_POLICY=' + json.dumps({'policy': p.to_dict(), 'llm': c.model_dump()}), flush=True)
result = run_agent('/run/task.json', '/run', '/run/policy.json' if __import__('pathlib').Path('/run/policy.json').exists() else None)
print('AGENT_RESULT=' + json.dumps({
    'run_id': result['result']['run_id'],
    'final_status': result['result']['final_status'],
    'patch_applied': result['result'].get('patch_applied', False),
    'duration_sec': result['result'].get('duration_sec'),
    'tool_stats': result['result'].get('tool_stats', {}),
}), flush=True)
'''
    cmd = ['docker','run','--rm','--network',network,'--read-only','--tmpfs','/tmp',
           '--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256',
           '--mount',f'type=bind,source={agent_export},target=/run/source,readonly',
           '--mount',f'type=bind,source={app_dir},target=/run/app,readonly',
           '--mount',f'type=bind,source={out/"task.json"},target=/run/task.json,readonly',
           '--mount',f'type=bind,source={logs},target=/run/logs',
           '-w','/run']
    if llm_env is not None:
        cmd += ['--env-file',str(llm_env),'-e','LLM_BASE_URL=http://model-proxy:8080',
                '--mount',f'type=bind,source={out/"policy.json"},target=/run/policy.json,readonly']
    if expected_model is not None:
        cmd += ['-e','REAL_ISSUE_EXPECTED_MODEL='+expected_model]
    if graph_enabled:
        cmd += ['--mount',f'type=bind,source={graph_dir},target=/opt/real_issue_graph,readonly',
                '--tmpfs','/run/.code_intelligence_shadow:exec','-e','HOME=/tmp']
    cmd += [image,agent_python,'-c',code]
    with (out/'agent_container.log').open('wb') as stream:
        completed = subprocess.run(cmd, stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
    if completed.returncode:
        raise RuntimeError(f'Agent container failed: {out/"agent_container.log"}')
    lines = [line.split('=',1)[1] for line in (out/'agent_container.log').read_text(
        encoding='utf-8', errors='replace').splitlines() if line.startswith('AGENT_RESULT=')]
    if len(lines) != 1:
        raise RuntimeError('missing Agent result marker')
    agent = json.loads(lines[0])
    effective = [json.loads(line.split('=',1)[1]) for line in (out/'agent_container.log').read_text(encoding='utf-8', errors='replace').splitlines() if line.startswith('EFFECTIVE_POLICY=')]
    if policy is not None:
        if len(effective) != 1 or agent['tool_stats'].get('policy_id') != policy['policy_id'] or agent['tool_stats'].get('llm_model') != expected_model:
            raise RuntimeError('Missing or inconsistent effective configuration')
        dump(out/'effective_policy.json', effective[0])
    if graph_enabled:
        graph = agent['tool_stats'].get('code_intelligence', {})
        if not graph.get('available') or '0.8.1' not in graph.get('backend_version', '') or not graph.get('metrics', {}).get('index_success'):
            raise RuntimeError('Graph indexing unavailable; do not count as comparable baseline')
    workspace = logs/'trajectories'/task_id/agent['run_id']/'workspace'
    candidate = out/'candidate.patch'
    # Windows Git may exceed MAX_PATH when the private run directory is deep.
    # Extract the diff inside a short Linux mount after the Agent has exited.
    extract = '''import pathlib, subprocess
data = subprocess.check_output([
    'git','-c','core.fileMode=false','-C','/workspace','diff','--binary',
    '--no-ext-diff','initial','--'])
pathlib.Path('/results/candidate.patch').write_bytes(data)
'''
    subprocess.run([
        'docker','run','--rm','--network','none','--read-only',
        '--mount',f'type=bind,source={workspace},target=/workspace,readonly',
        '--mount',f'type=bind,source={out},target=/results',
        image,'python','-c',extract],check=True)
    evaluator_accepted = False
    evaluator_reason = 'no production patch'
    if candidate.stat().st_size:
        try:
            evaluator_accepted = score(task_dir, candidate)['accepted']
            evaluator_reason = 'hidden and P2P verdict'
        except CandidateRejected as error:
            evaluator_reason = str(error)
    result = {
        'task_id': prep['task_id'], 'label': label,
        'agent_final_status': agent['final_status'],
        'agent_patch_applied': agent['patch_applied'],
        'agent_tool_stats': agent['tool_stats'],
        'agent_run_id': agent['run_id'],
        'agent_duration_sec': agent.get('duration_sec'),
        'elapsed_sec': round(time.monotonic()-started, 3),
        'policy_sha256': sha(out/'policy.json') if llm_env is not None else None,
        'expected_model': expected_model,
        'candidate_patch_sha256': sha(candidate),
        'evaluator_accepted': evaluator_accepted,
        'evaluator_reason': evaluator_reason,
        'final_success': evaluator_accepted,
        'agent_mounts': ['/run/source','/run/app','/run/task.json','/run/logs'] +
                        (['/run/policy.json'] if llm_env is not None else []) +
                        (['/opt/real_issue_graph', '/run/.code_intelligence_shadow'] if graph_enabled else []),
        'agent_network': network, 'agent_image_id': image_id,
    }
    dump(out/'pipeline_result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('task_dir', type=P)
    parser.add_argument('agent_export', type=P)
    parser.add_argument('app_dir', type=P)
    parser.add_argument('image')
    parser.add_argument('--label', required=True)
    parser.add_argument('--llm-env', type=P)
    parser.add_argument('--network', default='none')
    parser.add_argument('--policy', type=P)
    parser.add_argument('--expected-model')
    parser.add_argument('--graph-dir', type=P)
    args = parser.parse_args()
    print(json.dumps(run(args.task_dir.resolve(), args.agent_export.resolve(),
                         args.app_dir.resolve(), args.image, args.label,
                         args.llm_env.resolve() if args.llm_env else None, args.network,
                         json.loads(args.policy.read_text(encoding='utf-8')) if args.policy else None,
                         args.expected_model, graph_dir=args.graph_dir.resolve() if args.graph_dir else None)))
