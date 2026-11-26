"""Register only reviewed/admitted tasks using the existing Task schema.
Do not invoke until real validation, environment locking and isolation are audited.
"""
import argparse, json, pathlib, shutil, tempfile
from admission import CAT, dump, sha
from validate import apply
P=pathlib.Path


def read(p): return json.loads(p.read_text(encoding='utf-8'))


def check_task(private,t):
    root=private/t['task_id']; p=read(root/'prepared.json'); cfg=read(root/'review.json'); v=read(root/'validation.json'); audit=read(root/'audit.json')
    if p['base_commit']!=t['base_commit'] or p['merge_commit']!=t['merge_commit']: raise ValueError('base or merge drift')
    if cfg['status']!='reviewed' or v['status']!='test_matrix_passed_pending_audit' or v['task_id']!=t['task_id'] or v['checks']!={'f2p':True,'p2p':True,'hidden':True}: raise ValueError('test matrix incomplete')
    if v['review_sha256']!=sha(root/'review.json'): raise ValueError('review changed since validation')
    for k,h in v['patch_sha256'].items():
        if sha(root/cfg[k])!=h: raise ValueError(k+' changed since validation')
    if not v.get('lock_sha256') or any(sha(P(p))!=h for p,h in v['lock_sha256'].items()): raise ValueError('dependency lock missing or changed')
    gates=('issue_authenticity','semantic_dedup','patch_scope','reproduction','stable_tests','environment_locked','runtime_isolation','external_scoring')
    if not all(audit.get(k) is True for k in gates): raise ValueError('manual audit incomplete')
    if audit.get('validation_sha256') != sha(root/'validation.json'): raise ValueError('validation changed since audit')
    if not cfg.get('public_test_command') or not cfg.get('issue_title') or not cfg.get('issue_text'): raise ValueError('public task definition incomplete')
    if cfg['issue_text']==t['behavior']: raise ValueError('replace symptom-only draft with reviewed task statement')
    return root,cfg


def main():
    a=argparse.ArgumentParser(); a.add_argument('--private',required=True,type=P); a.add_argument('--project',required=True,type=P); args=a.parse_args(); private=args.private.resolve(); project=args.project.resolve()
    if private.is_relative_to(project) or project.is_relative_to(private): raise ValueError('evaluator data and project must be in separate directory trees')
    if not (project/'app/schemas/task_schema.py').is_file(): raise ValueError('project must be agentic-swe root')
    tasks=read(CAT)['tasks']; assert len(tasks)==20 and len({t['task_id'] for t in tasks})==20
    # Validate all 20 gates before writing anything.
    ready=[(t,*check_task(private,t)) for t in tasks]
    task_dir=project/'benchmarks/tasks/real_issue_full_v1'; repo_dir=project/'benchmarks/repos/real_issue_full_v1'; manifest=project/'benchmarks/manifests/real_issue_full_frozen_20_v1.json'
    if any(p.exists() for p in (task_dir,repo_dir,manifest)): raise FileExistsError('refuse to overwrite existing artifacts')
    task_paths=[]
    try:
        for t,root,cfg in ready:
            tid='real_full_'+t['task_id'].removeprefix('real_'); target=repo_dir/tid
            # Apply outside the Agent repository so git apply cannot resolve to its parent Git root.
            with tempfile.TemporaryDirectory(dir=root) as td:
                staged=P(td)/'repo'; shutil.copytree(root/'base_snapshot',staged,symlinks=True)
                apply(staged,root/cfg['visible_test_patch'])
                shutil.copytree(staged,target,symlinks=True)
            payload={'task_id':tid,'repo_name':t['repo_full_name'].split('/')[-1],'repo_path':target.relative_to(project).as_posix(),'issue_title':cfg['issue_title'],'issue_text':cfg['issue_text'],'test_command':cfg['public_test_command'],'success_criteria':cfg.get('public_success_criteria',t['behavior']),'difficulty':t['difficulty'],'tags':['bugfix','python','real-issue'],'target_files_hint':[],'expected_failure_test':cfg.get('visible_failure_test'),'max_retries':2,'source_type':'real_issue','metadata':{'test_command_source':'reviewed_visible_reproducer'}}
            path=task_dir/(tid+'.json'); dump(path,payload); task_paths.append(path.relative_to(project).as_posix())
        dump(manifest,{'manifest_id':'real_issue_full_frozen_20_v1','description':'20 independently admitted full real-repository tasks; external evaluator acceptance required.','tasks':task_paths})
    except Exception:
        for p in (task_dir,repo_dir):
            if p.exists(): shutil.rmtree(p)
        if manifest.exists(): manifest.unlink()
        raise
    return 0
if __name__=='__main__': raise SystemExit(main())
