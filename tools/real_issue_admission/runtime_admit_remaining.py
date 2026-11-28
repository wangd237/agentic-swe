"""Check the remaining task runtimes with the existing no-LLM Agent probe."""
import argparse
import json
import pathlib
import re
import subprocess

from admission import CAT, dump
from runtime_agent_probe import run

P = pathlib.Path


def output(*args):
    return subprocess.check_output(args, text=True).replace('\r\n', '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('private', type=P)
    parser.add_argument('exports', type=P)
    parser.add_argument('app', type=P)
    args = parser.parse_args()
    private, exports, app = (args.private.resolve(), args.exports.resolve(), args.app.resolve())
    tasks = json.loads(CAT.read_text(encoding='utf-8'))['tasks']
    dockerfile = P(__file__).with_name('Dockerfile.agent_runtime')
    existing = {}
    for task in tasks:
        root = private/task['task_id']
        cfg = json.loads((root/'review.json').read_text(encoding='utf-8'))
        runtime_path = root/'agent_runtime.json'
        if runtime_path.exists():
            runtime = json.loads(runtime_path.read_text(encoding='utf-8'))
            existing.setdefault(cfg['container_image'], runtime['image'])
    results = {}
    for task in tasks:
        task_id = task['task_id']
        if task_id == 'real_tomlkit_377':
            continue
        root = private/task_id
        cfg = json.loads((root/'review.json').read_text(encoding='utf-8'))
        base = cfg['container_image']
        image = existing.get(base)
        if image is None:
            tag = re.sub(r'[^a-z0-9]+', '-', base.lower()).strip('-')
            image = 'real-issue-agent-'+tag+':locked'
            print('BUILD', base, image, flush=True)
            subprocess.run(['docker','build','--build-arg','TASK_IMAGE='+base,
                            '-t',image,'-f',str(dockerfile),str(dockerfile.parent)],
                           check=True, stdout=subprocess.DEVNULL)
            existing[base] = image
        image_id = output('docker','image','inspect',image,'--format','{{.Id}}').strip()
        freeze = output('docker','run','--rm','--network','none',image,
                        'python','-m','pip','freeze','--all')
        runtime_path = root/'agent_runtime.json'
        lock_path = root/'agent_dependencies.lock.txt'
        if runtime_path.exists():
            locked = json.loads(runtime_path.read_text(encoding='utf-8'))
            if locked != {'image': image, 'image_id': image_id}:
                raise ValueError(task_id+' image lock drift')
            if lock_path.read_text(encoding='utf-8').replace('\r\n','\n') != freeze:
                raise ValueError(task_id+' dependency lock drift')
        else:
            dump(runtime_path, {'image':image,'image_id':image_id})
            lock_path.write_text(freeze, encoding='utf-8')
        probe_root = root/'runtime_agent_probe'
        completed_path = probe_root/'runtime_admission_1'/'pipeline_result.json'
        if completed_path.exists():
            result = json.loads(completed_path.read_text(encoding='utf-8'))
            if result['agent_image_id'] != image_id:
                raise ValueError(task_id+' completed probe image drift')
            print('REUSE', task_id, flush=True)
        else:
            label = 'runtime_admission_2' if (probe_root/'runtime_admission_1').exists() else 'runtime_admission_1'
            print('PROBE', task_id, label, flush=True)
            result = run(root, exports/task_id, app, image, label)
        if result['agent_tool_stats'].get('total_tool_calls', 0) < 1:
            raise ValueError(task_id+' Agent did not use tools')
        if result['agent_network'] != 'none' or result['final_success'] != result['evaluator_accepted']:
            raise ValueError(task_id+' unexpected runtime verdict')
        results[task_id] = {
            'agent_image_id': image_id,
            'agent_tool_calls': result['agent_tool_stats']['total_tool_calls'],
            'agent_network': result['agent_network'],
            'final_success': result['final_success'],
        }
        print('PASS', task_id, flush=True)
    dump(private/'runtime_admission_remaining.json', results)
    print('RUNTIME_ADMITTED', len(results), flush=True)


if __name__ == '__main__':
    main()
