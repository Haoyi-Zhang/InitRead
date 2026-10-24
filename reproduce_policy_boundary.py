"""Native owned-policy transfer control with a separately coded Python reference."""
import argparse, csv, io, itertools, json, os, platform, subprocess, sys
from pathlib import Path
from reproduce_java_conformance import tools, VM

ROOT=Path(__file__).resolve().parent

def reference():
    totals={p:dict(cases=0, final_accept=0, prefix_accept=0, final_only=0,
                   malformed_rejected=0, alias_checks=0) for p in ('tenant-quota','quorum')}
    for n in (1,2):
        for tenant,quota,links in itertools.product(itertools.product(range(2),repeat=n),
                itertools.product(range(3),repeat=n), itertools.product(range(-1,n),repeat=n)):
            for mask in range(1<<n):
                selected=[i for i in range(n) if mask & (1<<i)]
                for roots in itertools.permutations(selected):
                    closures=[]
                    for length in range(len(roots)+1):
                        live=set(roots[:length])
                        while True:
                            after=live | {links[i] for i in live if links[i]>=0}
                            if after==live: break
                            live=after
                        closures.append(live)
                    valid={
                        'tenant-quota':[all(links[i]<0 or
                            (tenant[i]==tenant[links[i]] and quota[links[i]]<=quota[i]) for i in k)
                            for k in closures],
                        'quorum':[not k or len(k)>=2 for k in closures]}
                    for p, decisions in valid.items():
                        row=totals[p]; final=decisions[-1]; prefix=all(decisions)
                        row['cases']+=1; row['final_accept']+=final; row['prefix_accept']+=prefix
                        row['final_only']+=final and not prefix
                        row['malformed_rejected']+=1; row['alias_checks']+=final
    return totals

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True,type=Path); ap.add_argument('--java-home')
    a=ap.parse_args(); out=a.out.resolve()
    if out.exists() or out==ROOT or ROOT in out.parents or out in ROOT.parents:
        ap.error('Use a fresh output directory outside the artifact')
    java,javac=tools(a.java_home); out.mkdir(parents=True); (out/'classes').mkdir()
    env=dict(os.environ)
    for k in ('JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','CLASSPATH'): env.pop(k,None)
    commands=[]
    def run(argv):
        r=subprocess.run(argv,env=env,capture_output=True,text=True,timeout=60,cwd=ROOT)
        commands.append({'argv':argv,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if r.returncode: raise RuntimeError(r.stderr)
        return r.stdout
    run([javac,'-proc:none','--release','17','-encoding','UTF-8','-d',str(out/'classes'),
         str(ROOT/'java/PolicyBoundaryStudy.java')])
    text=run([java,*VM,'-cp',str(out/'classes'),'PolicyBoundaryStudy'])
    native={r.pop('policy'):{k:int(v) for k,v in r.items()} for r in csv.DictReader(io.StringIO(text))}
    wanted=reference()
    if native!=wanted: raise AssertionError((native,wanted))
    if native['tenant-quota']['final_only'] or not native['quorum']['final_only']:
        raise AssertionError('policy boundary not demonstrated')
    (out/'rows.csv').write_text(text,encoding='utf-8')
    result={'status':'PASS','scope':'Owned post-primitive-decoding control, not a new serialized wire receiver or external deployment',
            'python':sys.version,'platform':platform.platform(),'policies':native,
            'reference_agreement':True,'original_receiver_modified':False,
            'counterexample':{'tenant':[0,0],'quota':[1,1],'next':[-1,-1],'roots':[0,1],
                 'policy':'empty or at least two reachable entries','prefix_decisions':[True,False,True]},
            'commands':commands}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','policies':native}))

if __name__=='__main__': main()
