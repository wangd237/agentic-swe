"""No-LLM smoke of Harness workspace setup and evaluator-owned acceptance.

The preset patch is applied only after the isolated Agent-side container exits.
This tests artifact transfer and final-status ownership without exposing the
reference patch to that container.
"""
import argparse
import json
import pathlib
import subprocess

from admission import dump, sha
from score import score
from validate import apply

P=pathlib.Path


def run(task_dir,agent_export,app_dir,preset_patch,label):
    cfg=json.loads((task_dir/'review.json').read_text(encoding='utf-8'))
    prep=json.loads((task_dir/'prepared.json').read_text(encoding='utf-8'))
    validation=json.loads((task_dir/'validation.json').read_text(encoding='utf-8'))
    if validation['status']!='test_matrix_passed_pending_audit':
        raise ValueError('task validation has not passed')
    if not agent_export.is_dir() or list(agent_export.rglob('.git')):
        raise ValueError('invalid Agent export')
    image=cfg['container_image']
    image_id=subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
    if image_id!=validation['container_image_id']:
        raise ValueError('container image drift')
    out=task_dir/'runtime_smoke'/label
    if out.exists(): raise FileExistsError(out)
    workspace=out/'workspace'
    workspace.mkdir(parents=True)
    command=cfg['public_test_command']
    if prep['repo_full_name']=='agronholm/anyio':
        command=command.replace('python -m pytest','python -m pytest -p anyio.pytest_plugin',1)
    code=("import json,sys; "
          "from app.runtime.harness import copy_repo_to_workspace; "
          "from app.tools.builtin.run_tests import run_tests; "
          "copy_repo_to_workspace('/source','/workspace',install_editable=False); "
          "r=run_tests('/workspace',sys.argv[1]); "
          "print('AGENT_VISIBLE_RESULT='+json.dumps({'ok':r['ok'],'exit_code':r['data'].get('exit_code')}))")
    cmd=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp',
         '--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256',
         '--mount',f'type=bind,source={agent_export},target=/source,readonly',
         '--mount',f'type=bind,source={app_dir},target=/runner_code/app,readonly',
         '--mount',f'type=bind,source={workspace},target=/workspace',
         '-e','PYTHONPATH=/runner_code:/source/src:/source',image,'python','-c',code,command]
    agent_log=out/'agent_container.log'
    with agent_log.open('wb') as f:
        completed=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=300)
    if completed.returncode:
        raise RuntimeError(f'Agent-side Harness smoke failed: {agent_log}')
    agent_output=agent_log.read_text(encoding='utf-8',errors='replace')
    lines=[x for x in agent_output.splitlines() if x.startswith('AGENT_VISIBLE_RESULT=')]
    if len(lines)!=1: raise RuntimeError('missing Agent visible result')
    visible=json.loads(lines[0].split('=',1)[1])
    # The preset is injected after the Agent container has exited; no preset
    # or Evaluator directory was mounted into that container.
    subprocess.run(['git','-C',str(workspace),'config','core.fileMode','false'],check=True)
    apply(workspace,preset_patch)
    candidate=out/'candidate.patch'
    # Windows bind mounts can report every source file as executable inside
    # Linux; ignore that host/container mode mismatch when extracting edits.
    candidate.write_bytes(subprocess.check_output(['git','-c','core.fileMode=false','-C',str(workspace),
                                                   'diff','--binary','--no-ext-diff','--']))
    if not candidate.stat().st_size: raise RuntimeError('preset produced no production diff')
    judged=score(task_dir,candidate)
    result={'task_id':prep['task_id'],'label':label,'agent_visible_result':visible,
            'candidate_patch_sha256':sha(candidate),'evaluator_accepted':judged['accepted'],
            'final_success':judged['accepted'],'image_id':image_id,
            'agent_mounts':['/source','/runner_code/app','/workspace'],
            'agent_network':'none'}
    dump(out/'pipeline_result.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('task_dir',type=P)
    parser.add_argument('agent_export',type=P)
    parser.add_argument('app_dir',type=P)
    parser.add_argument('preset_patch',type=P)
    parser.add_argument('--label',required=True)
    args=parser.parse_args()
    result=run(args.task_dir.resolve(),args.agent_export.resolve(),
               args.app_dir.resolve(),args.preset_patch.resolve(),args.label)
    print(json.dumps(result))
