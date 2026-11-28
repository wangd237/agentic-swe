"""Run the existing Agent entry in one locked task container."""
import argparse
import json
import pathlib
import subprocess

from admission import dump, sha
from score import score

P = pathlib.Path


def run(task_dir, agent_export, app_dir, image, label, llm_env=None, network='none'):
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
    out = task_dir/'runtime_agent_probe'/label
    if out.exists():
        raise FileExistsError(out)
    logs = out/'agent_logs'
    logs.mkdir(parents=True)
    task_id = 'probe_'+prep['task_id']
    command = cfg['public_test_command']
    if prep['repo_full_name'] == 'agronholm/anyio':
        command = command.replace('python -m pytest', 'python -m pytest -p anyio.pytest_plugin', 1)
    if prep['repo_full_name'] == 'pydantic/pydantic':
        command = command.replace('python -m pytest', '/usr/local/bin/python -m pytest -o addopts=', 1)
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
        dump(out/'policy.json', {
            'policy_id': 'real_issue_single_acceptance',
            'description': 'Single paid LLM runtime acceptance',
            'agent_type': 'llm', 'max_steps': 8,
            'llm_max_output_tokens': 4096,
            'llm_compaction_mode': 'rules',
            'llm_timeout_sec': 120,
            'llm_client_max_retries': 1,
        })
    code = '''import json
from app.runtime import task_runner
from app.agent import llm_agent
from app.runtime.agent_entry import run_agent

original = task_runner.copy_repo_to_workspace
def locked_copy(*args, **kwargs):
    return original(*args, install_editable=False, **kwargs)
task_runner.copy_repo_to_workspace = locked_copy
llm_agent.copy_repo_to_workspace = locked_copy
result = run_agent('/run/task.json', '/run', '/run/policy.json' if __import__('pathlib').Path('/run/policy.json').exists() else None)
print('AGENT_RESULT=' + json.dumps({
    'run_id': result['result']['run_id'],
    'final_status': result['result']['final_status'],
    'patch_applied': result['result'].get('patch_applied', False),
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
        except ValueError as error:
            evaluator_reason = str(error)
    result = {
        'task_id': prep['task_id'], 'label': label,
        'agent_final_status': agent['final_status'],
        'agent_patch_applied': agent['patch_applied'],
        'agent_tool_stats': agent['tool_stats'],
        'candidate_patch_sha256': sha(candidate),
        'evaluator_accepted': evaluator_accepted,
        'evaluator_reason': evaluator_reason,
        'final_success': evaluator_accepted,
        'agent_mounts': ['/run/source','/run/app','/run/task.json','/run/logs'] +
                        (['/run/policy.json'] if llm_env is not None else []),
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
    args = parser.parse_args()
    print(json.dumps(run(args.task_dir.resolve(), args.agent_export.resolve(),
                         args.app_dir.resolve(), args.image, args.label,
                         args.llm_env.resolve() if args.llm_env else None, args.network)))
