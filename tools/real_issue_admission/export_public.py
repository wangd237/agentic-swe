"""Build single-task Agent source exports from reviewed baselines and visible tests."""
import argparse
import json
import pathlib
import shutil
import tempfile

from admission import CAT, sha
from validate import apply

P = pathlib.Path


def export_task(root, target):
    cfg = json.loads((root/'review.json').read_text(encoding='utf-8'))
    validation = json.loads((root/'validation.json').read_text(encoding='utf-8'))
    if validation['status'] != 'test_matrix_passed_pending_audit':
        raise ValueError('task matrix not passed')
    if validation['review_sha256'] != sha(root/'review.json'):
        raise ValueError('review changed after validation')
    if target.exists():
        raise FileExistsError(target)
    with tempfile.TemporaryDirectory(dir=root) as td:
        staged = P(td)/'repo'
        shutil.copytree(root/'base_snapshot', staged, symlinks=True)
        apply(staged, root/cfg['visible_test_patch'])
        forbidden = {'.git', 'reference.patch', 'hidden.patch', 'review.json',
                     'validation.json', 'audit.json', 'catalog.evaluator.json'}
        if any(p.name in forbidden for p in staged.rglob('*')):
            raise ValueError('private or Git file in Agent export')
        shutil.copytree(staged, target, symlinks=True)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('private', type=P)
    parser.add_argument('destination', type=P)
    parser.add_argument('--task')
    args = parser.parse_args()
    private = args.private.resolve()
    destination = args.destination.resolve()
    if destination.is_relative_to(private) or private.is_relative_to(destination):
        raise ValueError('Agent export and Evaluator directory overlap')
    destination.mkdir(parents=True, exist_ok=True)
    tasks = json.loads(CAT.read_text(encoding='utf-8'))['tasks']
    chosen = [t for t in tasks if not args.task or t['task_id'] == args.task]
    if not chosen:
        raise ValueError('unknown task')
    for task in chosen:
        target = destination/task['task_id']
        if target.exists():
            print(task['task_id'], 'already exists; preserved')
            continue
        export_task(private/task['task_id'], target)
        print(task['task_id'], 'exported')


if __name__ == '__main__':
    main()
