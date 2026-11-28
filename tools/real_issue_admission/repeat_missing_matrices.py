"""Fill missing second-pass matrix records before the final stability audit."""
import json
import pathlib
import subprocess
import sys

from admission import CAT

P = pathlib.Path


def main(private):
    tasks = json.loads(CAT.read_text(encoding='utf-8'))['tasks']
    for task in tasks:
        root = private/task['task_id']
        repeat = root/'validation_repeat1.json'
        if repeat.exists():
            continue
        original_path = root/'validation.json'
        original_bytes = original_path.read_bytes()
        original = json.loads(original_bytes.decode('utf-8'))
        print('REPEAT', task['task_id'], flush=True)
        try:
            subprocess.run([sys.executable,str(P(__file__).with_name('validate.py')),
                            str(root)], check=True)
            repeated_bytes = original_path.read_bytes()
            repeated = json.loads(repeated_bytes.decode('utf-8'))
            if repeated['results'] != original['results'] or repeated['checks'] != original['checks']:
                raise ValueError(task['task_id']+' matrix changed on repeat')
            repeat.write_bytes(repeated_bytes)
            print('STABLE', task['task_id'], flush=True)
        finally:
            original_path.write_bytes(original_bytes)


if __name__ == '__main__':
    main(P(sys.argv[1]).resolve())
