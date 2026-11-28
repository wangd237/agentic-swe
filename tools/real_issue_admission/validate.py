"""Run reviewed tests against clean baseline and reference patch; keep logs private."""
import argparse, json, os, pathlib, shutil, subprocess, tempfile, xml.etree.ElementTree as ET
from admission import dump, sha
P=pathlib.Path

def apply(root,patch):
    if patch and patch.stat().st_size:
        # A private staging directory can still sit below an unrelated Git worktree.
        # Stop discovery at its parent so patch paths resolve against this copy.
        env = {**os.environ, 'GIT_CEILING_DIRECTORIES': str(root.parent.resolve())}
        subprocess.run(['git','apply','--check',str(patch)],cwd=root,check=True,env=env)
        subprocess.run(['git','apply',str(patch)],cwd=root,check=True,env=env)

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

def read_junit(xml):
    cases={}
    for case in ET.parse(xml).iter('testcase'):
        name=case.get('classname','')+'::'+case.get('name','')
        if name in cases: raise ValueError('duplicate junit node: '+name)
        if case.find('error') is not None: raise RuntimeError('test setup/collection error: '+name)
        cases[name]='fail' if case.find('failure') is not None else 'skip' if case.find('skipped') is not None else 'pass'
    if not cases or not any(x!='skip' for x in cases.values()): raise RuntimeError('no executed tests')
    return cases

def container_tests(image,module,work,args,log,runner='pytest'):
    xml=log.with_suffix('.xml')
    if xml.exists(): xml.unlink()
    if runner == 'pytest':
        code=("import importlib.util,pathlib,pytest,sys; "
              "p=pathlib.Path(importlib.util.find_spec(sys.argv[1]).origin).resolve(); "
              "assert p.is_relative_to(pathlib.Path('/task')), p; "
              "print('source:',p,flush=True); "
              "raise SystemExit(pytest.main(sys.argv[2:]))")
        tail=['-p','no:cacheprovider',*args,'--junitxml','/results/'+xml.name]
    elif runner == 'unittest':
        if len(args) != 1 or not args[0].startswith('testing/') or not args[0].endswith('.py'):
            raise ValueError('unittest runner requires one testing/*.py path')
        code='''import importlib.util
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET

source = pathlib.Path(importlib.util.find_spec(sys.argv[1]).origin).resolve()
assert source.is_relative_to(pathlib.Path('/task')), source
print('source:', source, flush=True)

class Capture(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = {}

    def startTest(self, test):
        super().startTest(test)
        self.cases[test.id()] = ('pass', '')

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.cases[test.id()] = ('fail', self._exc_info_to_string(error, test))

    def addError(self, test, error):
        super().addError(test, error)
        status = 'error' if test.__class__.__name__ == '_FailedTest' else 'fail'
        self.cases[test.id()] = (status, self._exc_info_to_string(error, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.cases[test.id()] = ('skip', reason)

suite = unittest.defaultTestLoader.discover(
    '/task/testing', pattern=pathlib.Path(sys.argv[2]).name
)
result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2, resultclass=Capture).run(suite)
root = ET.Element('testsuite')
for name, (status, message) in result.cases.items():
    cls, _, method = name.rpartition('.')
    case = ET.SubElement(root, 'testcase', classname=cls, name=method)
    if status != 'pass':
        tag = {'fail': 'failure', 'error': 'error', 'skip': 'skipped'}[status]
        ET.SubElement(case, tag).text = message
ET.ElementTree(root).write(sys.argv[3], encoding='utf-8', xml_declaration=True)
raise SystemExit(0 if result.wasSuccessful() else 1)
'''
        tail=[args[0],'/results/'+xml.name]
    else:
        raise ValueError('unsupported test runner')
    cmd=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp',
         '--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256',
         '--mount',f'type=bind,source={work},target=/task,readonly',
         '--mount',f'type=bind,source={log.parent},target=/results',
         '-e','PYTHONPATH=/task/src:/task','-w','/task',image,'python','-c',code,module,
         *tail]
    with log.open('wb') as out:
        result=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,timeout=900)
    if result.returncode not in (0,1) or not xml.exists():
        raise RuntimeError(f'invalid container test execution: {log}, exit={result.returncode}')
    return read_junit(xml)

def compare(before,after,mode):
    if before.keys()!=after.keys(): return False
    if mode=='p2p': return all(before[k]==after[k]=='pass' for k in before)
    return 'fail' in before.values() and all(after[k]=='pass' for k in after) and all(x in ('pass','fail') for x in before.values())

def main():
    a=argparse.ArgumentParser(); a.add_argument('task_dir',type=P); args=a.parse_args(); root=args.task_dir.resolve(); cfg=json.loads((root/'review.json').read_text()); prep=json.loads((root/'prepared.json').read_text())
    if cfg['status']!='reviewed': raise ValueError('review.json must be reviewed first')
    container=bool(cfg.get('container_image'))
    required=['lock_files','visible_test_patch','hidden_test_patch','reference_patch','f2p_args','p2p_args','hidden_args']
    if not container: required+=['python_executable','install_args']
    for key in required:
        if not cfg.get(key): raise ValueError('missing '+key)
    if cfg['visible_test_patch']==cfg['hidden_test_patch']: raise ValueError('visible and hidden patches must differ')
    logs=root/'validation'; logs.mkdir(exist_ok=True); results={}
    lock_hashes={str(P(p).resolve()):sha(P(p).resolve()) for p in cfg['lock_files']}
    process_env={**os.environ,**cfg.get('build_env',{})}
    if container:
        image=cfg['container_image']
        image_id=subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
        if image_id!=cfg.get('container_image_id'): raise ValueError('container image digest drift')
        python_version=subprocess.check_output(['docker','run','--rm','--network','none',image,'python','--version'],text=True).strip()
        freeze=subprocess.check_output(['docker','run','--rm','--network','none',image,'python','-m','pip','freeze','--all'],text=True)
        if freeze.replace('\r\n','\n')!=P(cfg['lock_files'][0]).read_text().replace('\r\n','\n'):
            raise ValueError('container dependency lock drift')
    else:
        python_version=subprocess.check_output([cfg['python_executable'],'--version'],stderr=subprocess.STDOUT,text=True).strip()

    for mode in ('f2p','p2p','hidden'):
        for version in ('before','after'):
            with tempfile.TemporaryDirectory(dir=root) as td:
                work=P(td)/'repo'; shutil.copytree(root/'base_snapshot',work,symlinks=True)
                if version=='after': apply(work,root/cfg['reference_patch'])
                if mode=='f2p': apply(work,root/cfg['visible_test_patch'])
                elif mode=='hidden': apply(work,root/cfg['hidden_test_patch'])
                elif mode=='p2p' and cfg.get('p2p_test_patch'):
                    apply(work,root/cfg['p2p_test_patch'])
                if container:
                    module=cfg.get('import_module') or prep['repo_full_name'].split('/')[-1]
                    results[f'{mode}_{version}']=container_tests(image,module,work,cfg[mode+'_args'],logs/f'{mode}_{version}.log',cfg.get('test_runner','pytest'))
                else:
                    env=P(td)/'venv'; subprocess.run([cfg['python_executable'],'-m','venv',str(env)],check=True)
                    python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
                    with (logs/f'{mode}_{version}_install.log').open('wb') as out:
                        subprocess.run([str(python),'-m','pip',*cfg['install_args']],cwd=work,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=900,env=process_env)
                    results[f'{mode}_{version}']=check_tests(python,work,cfg[mode+'_args'],logs/f'{mode}_{version}.log',env=process_env)
    if any(sha(P(p))!=h for p,h in lock_hashes.items()): raise ValueError('dependency lock changed during validation')
    checks={m:compare(results[m+'_before'],results[m+'_after'],m) for m in ('f2p','p2p','hidden')}
    patch_keys=['reference_patch','visible_test_patch','hidden_test_patch']
    if cfg.get('p2p_test_patch'): patch_keys.append('p2p_test_patch')
    dump(root/'validation.json',{'task_id':prep['task_id'],'status':'test_matrix_passed_pending_audit' if all(checks.values()) else 'failed','checks':checks,'results':results,'review_sha256':sha(root/'review.json'),'python_version':python_version,'container_image_id':image_id if container else None,'lock_sha256':lock_hashes,'patch_sha256':{k:sha(root/cfg[k]) for k in patch_keys}})
    return int(not all(checks.values()))
if __name__=='__main__': raise SystemExit(main())
