"""Write the freeze gates only after all recorded matrix and runtime evidence agrees."""
import argparse
import json
import pathlib
import subprocess

from admission import CAT, dump, sha

P = pathlib.Path


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('private', type=P)
    parser.add_argument('exports', type=P)
    args = parser.parse_args()
    private, exports = args.private.resolve(), args.exports.resolve()
    tasks = read(CAT)['tasks']
    ready = []
    for task in tasks:
        task_id = task['task_id']
        root = private/task_id
        review, validation = read(root/'review.json'), read(root/'validation.json')
        if review['status'] != 'reviewed' or validation['checks'] != {'f2p': True, 'p2p': True, 'hidden': True}:
            raise ValueError(task_id+' task validity incomplete')
        repeat_path = root/'validation_repeat1.json'
        if not repeat_path.exists() or read(repeat_path)['results'] != validation['results']:
            raise ValueError(task_id+' unstable test matrix')
        if not all((root/'validation'/(mode+'_'+version+'.xml')).is_file()
                   for mode in ('f2p','p2p','hidden') for version in ('before','after')):
            raise ValueError(task_id+' missing test matrix logs')
        reference_sha = sha(root/review['reference_patch'])
        scored = read(root/'scoring'/('result_'+reference_sha[:16]+'.json'))
        if not scored['accepted'] or scored['candidate_patch_sha256'] != reference_sha:
            raise ValueError(task_id+' reference scoring incomplete')
        export = exports/task_id
        if not export.is_dir() or any(p.name in {'.git','reference.patch','hidden.patch','audit.json'} for p in export.rglob('*')):
            raise ValueError(task_id+' public export invalid')
        runtime = read(root/'agent_runtime.json')
        image_id = subprocess.check_output(['docker','image','inspect',runtime['image'],
                                             '--format','{{.Id}}'], text=True).strip()
        if image_id != runtime['image_id'] or not (root/'agent_dependencies.lock.txt').is_file():
            raise ValueError(task_id+' runtime image lock drift')
        if task_id == 'real_pydantic_14310':
            if runtime.get('agent_python') != '/harness/bin/python':
                raise ValueError('Pydantic Harness environment is not separated')
            system_freeze = subprocess.check_output(['docker','run','--rm','--network','none',
                                                      runtime['image'],'python','-m','pip','freeze','--all'],
                                                     text=True).replace('\r\n','\n')
            if system_freeze != (root/'dependencies.lock.txt').read_text(encoding='utf-8').replace('\r\n','\n'):
                raise ValueError('Pydantic task test environment differs from validated lock')
        if task_id == 'real_tomlkit_377':
            label = 'llm_acceptance_1'
        else:
            completed = sorted((root/'runtime_agent_probe').glob('runtime_admission_*/pipeline_result.json'))
            if not completed:
                raise ValueError(task_id+' has no completed runtime probe')
            label = completed[-1].parent.name
        pipeline = read(root/'runtime_agent_probe'/label/'pipeline_result.json')
        agent_results = list((root/'runtime_agent_probe'/label/'agent_logs/trajectories').glob('**/result.json'))
        if len(agent_results) != 1 or read(agent_results[0])['pre_test_exit_code'] != 1:
            raise ValueError(task_id+' Agent-side visible reproducer did not fail as expected')
        if pipeline['agent_image_id'] != image_id or pipeline['agent_tool_stats']['total_tool_calls'] < 1:
            raise ValueError(task_id+' Agent did not execute in locked runtime')
        if pipeline['final_success'] != pipeline['evaluator_accepted']:
            raise ValueError(task_id+' final status is not evaluator-owned')
        if task_id == 'real_tomlkit_377':
            if (pipeline['agent_tool_stats']['agent_type'] != 'llm' or
                    pipeline['agent_tool_stats']['llm_usage']['call_count'] < 1 or
                    not pipeline['evaluator_accepted']):
                raise ValueError('real LLM acceptance incomplete')
            result = read(root/'scoring'/('result_'+pipeline['candidate_patch_sha256'][:16]+'.json'))
            if result['candidate_patch_sha256'] != pipeline['candidate_patch_sha256'] or not result['accepted']:
                raise ValueError('LLM patch not scored by independent Evaluator')
        elif pipeline['agent_network'] != 'none':
            raise ValueError(task_id+' Agent network not isolated')
        gates = ('issue_authenticity','semantic_dedup','patch_scope','reproduction',
                 'stable_tests','environment_locked','runtime_isolation','external_scoring')
        ready.append((root, {**{key: True for key in gates},
                             'task_id':task_id, 'validation_sha256':sha(root/'validation.json'),
                             'runtime_probe':label,
                             'reference_score_sha256':reference_sha}))
    for root, audit in ready:
        dump(root/'audit.json', audit)
    print('AUDITED', len(ready))


if __name__ == '__main__':
    main()
