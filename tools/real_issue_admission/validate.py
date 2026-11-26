"""Run reviewed tests against clean baseline and reference patch; keep logs private."""
import argparse, json, os, pathlib, shutil, subprocess, tempfile, xml.etree.ElementTree as ET
from admission import dump, sha
P=pathlib.Path

def apply(root,patch):
    if patch and patch.stat().st_size: subprocess.run(['git','apply','--check',str(patch)],cwd=root,check=True); subprocess.run(['git','apply',str(patch)],cwd=root,check=True)

def check_tests(python,root,args,log,env=None):
    xml=log.with_suffix('.xml')
    if xml.exists(): xml.unlink()
    cmd=[str(python),'-m','pytest',*args,'--junitxml',str(xml)]
    with log.open('wb') as out: r=subprocess.run(cmd,cwd=root,stdout=out,stderr=subprocess.STDOUT,timeout=600,env=env)
    if r.returncode not in (0,1) or not xml.exists(): raise RuntimeError(f'invalid pytest execution: {log}, exit={r.returncode}')
    cases={}
    for case in ET.parse(xml).iter('testcase'):
        name=case.get('classname','')+'::'+case.get('name','')
        if name in cases: raise ValueError('duplicate junit node: '+name)
        if case.find('error') is not None: raise RuntimeError('test setup/collection error: '+name)
        cases[name]='fail' if case.find('failure') is not None else 'skip' if case.find('skipped') is not None else 'pass'
    if not cases or not any(x!='skip' for x in cases.values()): raise RuntimeError('no executed tests')
    return cases

def compare(before,after,mode):
    if before.keys()!=after.keys(): return False
    if mode=='p2p': return all(before[k]==after[k]=='pass' for k in before)
    return 'fail' in before.values() and all(after[k]=='pass' for k in after) and all(x in ('pass','fail') for x in before.values())

def main():
    a=argparse.ArgumentParser(); a.add_argument('task_dir',type=P); args=a.parse_args(); root=args.task_dir.resolve(); cfg=json.loads((root/'review.json').read_text()); prep=json.loads((root/'prepared.json').read_text())
    if cfg['status']!='reviewed': raise ValueError('review.json must be reviewed first')
    for key in ['python_executable','install_args','lock_files','visible_test_patch','hidden_test_patch','reference_patch','f2p_args','p2p_args','hidden_args']:
        if not cfg.get(key): raise ValueError('missing '+key)
    if cfg['visible_test_patch']==cfg['hidden_test_patch']: raise ValueError('visible and hidden patches must differ')
    logs=root/'validation'; logs.mkdir(exist_ok=True); results={}
    lock_hashes={str(P(p).resolve()):sha(P(p).resolve()) for p in cfg['lock_files']}
    process_env={**os.environ,**cfg.get('build_env',{})}
    python_version=subprocess.check_output([cfg['python_executable'],'--version'],stderr=subprocess.STDOUT,text=True).strip()

    for mode in ('f2p','p2p','hidden'):
        for version in ('before','after'):
            with tempfile.TemporaryDirectory(dir=root) as td:
                work=P(td)/'repo'; shutil.copytree(root/'base_snapshot',work,symlinks=True)
                if version=='after': apply(work,root/cfg['reference_patch'])
                if mode=='f2p': apply(work,root/cfg['visible_test_patch'])
                elif mode=='hidden': apply(work,root/cfg['hidden_test_patch'])
                env=P(td)/'venv'; subprocess.run([cfg['python_executable'],'-m','venv',str(env)],check=True)
                python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
                with (logs/f'{mode}_{version}_install.log').open('wb') as out:
                    subprocess.run([str(python),'-m','pip',*cfg['install_args']],cwd=work,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=900,env=process_env)
                results[f'{mode}_{version}']=check_tests(python,work,cfg[mode+'_args'],logs/f'{mode}_{version}.log',env=process_env)
    if any(sha(P(p))!=h for p,h in lock_hashes.items()): raise ValueError('dependency lock changed during validation')
    checks={m:compare(results[m+'_before'],results[m+'_after'],m) for m in ('f2p','p2p','hidden')}
    dump(root/'validation.json',{'task_id':prep['task_id'],'status':'test_matrix_passed_pending_audit' if all(checks.values()) else 'failed','checks':checks,'results':results,'review_sha256':sha(root/'review.json'),'python_version':python_version,'lock_sha256':lock_hashes,'patch_sha256':{k:sha(root/cfg[k]) for k in ('reference_patch','visible_test_patch','hidden_test_patch')}})
    return int(not all(checks.values()))
if __name__=='__main__': raise SystemExit(main())
