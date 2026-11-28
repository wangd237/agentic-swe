"""Evaluator-owned acceptance of a production patch; never run in Agent workspace."""
import argparse
import json
import pathlib
import shutil
import subprocess
import tempfile

from admission import dump, sha
from validate import apply, container_tests

P = pathlib.Path


def changed_paths(patch):
    data = subprocess.check_output(['git', 'apply', '--numstat', '-z', str(patch)])
    paths = []
    for record in data.split(b'\0'):
        if record:
            fields = record.decode('utf-8').split('\t')
            if len(fields) != 3:
                raise ValueError('unsupported patch path or rename')
            paths.append(fields[2])
    return paths


def score(root, patch):
    cfg = json.loads((root/'review.json').read_text(encoding='utf-8'))
    prep = json.loads((root/'prepared.json').read_text(encoding='utf-8'))
    validated = json.loads((root/'validation.json').read_text(encoding='utf-8'))
    if validated['status'] != 'test_matrix_passed_pending_audit':
        raise ValueError('task has no passing validation matrix')
    if validated['review_sha256'] != sha(root/'review.json'):
        raise ValueError('review changed after validation')
    if any(sha(root/cfg[key]) != digest for key,digest in validated['patch_sha256'].items()):
        raise ValueError('evaluation patch changed after validation')
    if any(sha(P(p)) != h for p,h in validated['lock_sha256'].items()):
        raise ValueError('dependency lock drift')
    image = cfg['container_image']
    image_id = subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
    if image_id != validated['container_image_id']:
        raise ValueError('container image drift')
    paths = changed_paths(patch)
    source_roots = {p.split('/')[0] if not p.startswith('src/') else '/'.join(p.split('/')[:2])
                    for p in prep['source_files']}
    if not paths or any(not any(p.startswith(prefix+'/') for prefix in source_roots) for p in paths):
        raise ValueError('candidate patch changes files outside production source roots')
    out = root/'scoring'; out.mkdir(exist_ok=True)
    results={}
    module=cfg.get('import_module') or prep['repo_full_name'].split('/')[-1]
    runner=cfg.get('test_runner','pytest')
    for mode,test_patch in (('hidden',cfg['hidden_test_patch']),('p2p',cfg.get('p2p_test_patch'))):
        with tempfile.TemporaryDirectory(dir=root) as td:
            work=P(td)/'repo'
            shutil.copytree(root/'base_snapshot',work,symlinks=True)
            apply(work,patch)
            if test_patch:
                apply(work,root/test_patch)
            results[mode]=container_tests(image,module,work,cfg[mode+'_args'],out/(mode+'.log'),runner)
    hidden=results['hidden']
    p2p=results['p2p']
    accepted=all(s=='pass' for s in (*hidden.values(),*p2p.values()))
    result={'task_id':prep['task_id'],'accepted':accepted,'candidate_patch_sha256':sha(patch),
            'hidden_count':len(hidden),'p2p_count':len(p2p),'container_image_id':image_id}
    dump(out/('result_'+result['candidate_patch_sha256'][:16]+'.json'),result)
    dump(out/'result.json',result)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('task_dir',type=P)
    parser.add_argument('candidate_patch',type=P)
    args=parser.parse_args()
    result=score(args.task_dir.resolve(),args.candidate_patch.resolve())
    print(json.dumps(result))
    raise SystemExit(0 if result['accepted'] else 1)
