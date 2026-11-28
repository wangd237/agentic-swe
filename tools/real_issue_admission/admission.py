"""Evaluator-only staging and validation. No LLM calls; no automatic freeze."""
import argparse, configparser, hashlib, json, os, pathlib, re, subprocess, sys, tarfile, tempfile, shutil
P=pathlib.Path
CAT=P(__file__).with_name('catalog.evaluator.json')

def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(cwd,*args):
    return subprocess.check_output(['git','-C',str(cwd),*args])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def export(repo,commit,dst):
    dst.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryFile() as f:
        subprocess.run(['git','-C',str(repo),'archive',commit],stdout=f,check=True); f.seek(0)
        with tarfile.open(fileobj=f) as t: t.extractall(dst,filter='data')

def export_submodules(repo,commit,dst):
    """Materialize pinned gitlinks omitted by git archive, or fail preparation."""
    entries=git(repo,'ls-tree','-r','-z',commit).split(b'\0')
    links=[]
    for entry in entries:
        if not entry: continue
        meta,path=entry.split(b'\t',1)
        mode,kind,sha1=meta.decode().split()
        if mode=='160000': links.append((path.decode(),sha1))
    if not links: return {}
    cfg=configparser.ConfigParser(); cfg.read(dst/'.gitmodules',encoding='utf-8')
    sources={v.get('path'):v.get('url') for k,v in cfg.items() if k.startswith('submodule ')}
    resolved={}
    for path,sha1 in links:
        url=sources.get(path)
        if not url or not url.startswith('https://github.com/'):
            raise ValueError('Unreviewed submodule URL: '+path)
        target=(dst/path).resolve()
        if not target.is_relative_to(dst.resolve()): raise ValueError('Invalid submodule path: '+path)
        # git archive creates an empty directory for a gitlink.
        if target.exists():
            if any(target.iterdir()): raise ValueError('Submodule target is not empty: '+path)
            target.rmdir()
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(['git','init',td],check=True,stdout=subprocess.DEVNULL)
            subprocess.run(['git','-C',td,'remote','add','origin',url],check=True)
            subprocess.run(['git','-C',td,'fetch','--no-tags','--depth=1','origin',sha1],check=True)
            export(td,sha1,target)
        resolved[path]=sha1
    return resolved

def prepare(t,private):
    root=private/t['task_id']; root.mkdir(exist_ok=False,parents=True)
    repo=root/'upstream'; subprocess.run(['git','init',str(repo)],check=True)
    git(repo,'remote','add','origin','https://github.com/'+t['repo_full_name']+'.git')
    git(repo,'fetch','--no-tags','--depth=2','origin',t['merge_commit'])
    base=git(repo,'rev-parse',t['merge_commit']+'^1').decode().strip()
    if base != t['base_commit']: raise ValueError('Merge first parent differs from verified catalog; stop and review')
    paths=git(repo,'diff','--no-renames','--name-only','-z',base,t['merge_commit']).decode().split('\0'); paths=[x for x in paths if x]
    tests=[x for x in paths if x in t['upstream_test_files'] or x.startswith(('tests/','testing/','test/')) or '/_tests/' in x or '/tests/' in x]
    docs=[x for x in paths if x not in tests and (x.startswith(('docs/','doc/','changelog/','changelog.d/','newsfragments/')) or x.split('/')[-1].lower().startswith(('changelog','changes','authors')))]
    source=[x for x in paths if x not in tests+docs]
    if not source or not tests: raise ValueError('No source or test diff; review merge')
    for name,group in [('reference.patch',source),('upstream_tests.patch',tests),('other.patch',docs)]:
        (root/name).write_bytes(git(repo,'diff','--binary','--no-renames',base,t['merge_commit'],'--',*group) if group else b'')
    export(repo,base,root/'base_snapshot')
    submodules=export_submodules(repo,base,root/'base_snapshot')
    data={**t,'base_commit':base,'base_matches_observed':base==t['observed_pr_base'],'source_files':source,'test_files':tests,'other_files':docs,'submodules':submodules,'patch_sha256':{name:sha(root/name) for name in ('reference.patch','upstream_tests.patch','other.patch')},'status':'prepared_not_validated'}
    dump(root/'prepared.json',data)
    dump(root/'review.json',{'status':'needs_review','python_executable':None,'install_args':None,'lock_files':[],'build_env':{},'visible_test_patch':None,'hidden_test_patch':'upstream_tests.patch','reference_patch':'reference.patch','f2p_args':None,'p2p_args':None,'hidden_args':None,'issue_title':None,'issue_text':t['behavior'],'public_test_command':None,'public_success_criteria':t['behavior'],'review_notes':t['risk']})
    return data

def main():
    a=argparse.ArgumentParser(); a.add_argument('--private',required=True,type=P,help='Evaluator-only directory outside agent-accessible repository'); a.add_argument('--task',action='append'); args=a.parse_args()
    private=args.private.resolve(); private.mkdir(parents=True,exist_ok=True)
    tasks=json.loads(CAT.read_text())['tasks']; chosen=[t for t in tasks if not args.task or t['task_id'] in args.task]
    if not chosen or (args.task and set(args.task)!={t['task_id'] for t in chosen}): a.error('unknown task')
    results=[]
    for t in chosen:
        try: results.append(prepare(t,private))
        except Exception as e: results.append({'task_id':t['task_id'],'status':'blocked','error':str(e)})
    dump(private/'preparation_report.json',results)
    return int(any(t['status']=='blocked' for t in results))
if __name__=='__main__': raise SystemExit(main())
