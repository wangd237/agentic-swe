"""Read-only structural preflight for every prepared Real Issue candidate."""
import argparse
import json
import os
import pathlib
import subprocess

from admission import CAT, dump, sha

P = pathlib.Path


def inspect(root):
    prep=json.loads((root/'prepared.json').read_text(encoding='utf-8'))
    base=root/'base_snapshot'
    env={**os.environ,'GIT_CEILING_DIRECTORIES':str(base.parent.resolve())}
    patches={}
    for name in ('reference.patch','upstream_tests.patch','other.patch'):
        path=root/name
        expected=prep['patch_sha256'][name]
        check=subprocess.run(['git','apply','--check',str(path)],cwd=base,env=env,
                             capture_output=True,text=True) if path.stat().st_size else None
        patches[name]={'hash_ok':sha(path)==expected,
                       'applies':check is None or check.returncode==0,
                       'error':(check.stderr.strip() if check and check.returncode else '')}
    gitlinks=subprocess.check_output(['git','-C',str(root/'upstream'),'ls-tree','-r',
                                      prep['base_commit']],text=True)
    missing=[]
    for line in gitlinks.splitlines():
        if line.startswith('160000 '):
            path=line.split('\t',1)[1]
            target=base/path
            if not target.is_dir() or not any(target.iterdir()): missing.append(path)
    return {'task_id':prep['task_id'],'base_exists':base.is_dir(),
            'source_files':prep['source_files'],'test_files':prep['test_files'],
            'missing_submodules':missing,'patches':patches,
            'structural_ok':base.is_dir() and not missing and all(
                p['hash_ok'] and p['applies'] for p in patches.values())}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('private',type=P)
    args=parser.parse_args()
    catalog=json.loads(CAT.read_text(encoding='utf-8'))
    roots=[args.private.resolve()/task['task_id'] for task in catalog['tasks']]
    report=[inspect(root) for root in roots]
    dump(args.private/'structural_preflight.json',report)
    print(json.dumps({'count':len(report),'passed':sum(r['structural_ok'] for r in report),
                      'failed':[r['task_id'] for r in report if not r['structural_ok']]}))
