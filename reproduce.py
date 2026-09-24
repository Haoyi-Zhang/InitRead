#!/usr/bin/env python3
"""Reproduce the owned bounded experiment, without downloading or contacting anything.

Python standard library, Linux, and a local JDK are sufficient. One experiment
worker is used; javac/java run sequentially, never concurrently with enumeration.
Output is written only into a fresh directory selected with --out.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from checker import Checker
from exhaustive import run as exhaustive_run
from oracle import exact
from producer import initial_cache, produce
from redundant_control import run as redundant_run
from witness import bfs, enumerated_oracle

MEASUREMENT_KEYS = {'cpu_seconds', 'wall_seconds', 'peak_rss_kib',
                    'parent_peak_rss_kib', 'child_peak_rss_kib', 'aggregate_rss_upper_kib'}

def semantic(x):
    if isinstance(x, dict):
        return {k: semantic(v) for k, v in x.items() if k not in MEASUREMENT_KEYS}
    if isinstance(x, list):
        return [semantic(v) for v in x]
    return x

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def measured_process(command, timeout, output):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.perf_counter()
    with output.open('w', encoding='utf-8') as stream:
        proc = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.PIPE,
                              text=True, timeout=timeout, check=False,
                              env={**os.environ, 'OMP_NUM_THREADS':'1', 'OPENBLAS_NUM_THREADS':'1',
                                   'MKL_NUM_THREADS':'1', 'JAVA_TOOL_OPTIONS':''})
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    if proc.returncode:
        raise RuntimeError(f'command failed (exit {proc.returncode}): {proc.stderr[-4000:]}')
    return {'cpu_seconds': after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
            'wall_seconds': time.perf_counter()-start,
            # Linux maximum over children seen so far, NOT an isolated per-stage measurement.
            'child_peak_rss_kib': after.ru_maxrss}

def verify(reference, actual):
    checked=[]
    for name in ['exhaustive-2.json', 'exhaustive-3.json', 'witnesses.json',
                 'java-summary.json', 'capacity.json', 'redundant-predicate.json', 'unit-summary.json']:
        expected=json.loads((reference/name).read_text())
        obtained=json.loads((actual/name).read_text())
        if semantic(expected)!=semantic(obtained):
            raise AssertionError(f'scientific mismatch: {name}')
        checked.append(name)
    for name in ['exhaustive-2-states.csv','exhaustive-3-states.csv','java-observations.jsonl',
                 'certificate-128.json','summary.csv']:
        if (reference/name).read_bytes()!=(actual/name).read_bytes():
            raise AssertionError(f'deterministic data mismatch: {name}')
        checked.append(name)
    return checked

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path, help='fresh or empty output directory')
    parser.add_argument('--verify-against', type=Path, help='compare scientific results, not timing/RSS')
    args=parser.parse_args()
    out=args.out.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error('--out must be empty; archived evidence is not overwritten')
    out.mkdir(parents=True,exist_ok=True)
    contract=json.loads((ROOT/'inputs/domain.json').read_text())
    if contract['object_counts'] != [2,3] or contract['checker_sampling_stride'] != 1:
        raise ValueError('the implemented audit and input contract do not match')
    begin=time.perf_counter(); own_begin=time.process_time()
    children_begin=resource.getrusage(resource.RUSAGE_CHILDREN)
    stages=[]
    unit_cpu, unit_wall = time.process_time(), time.perf_counter()
    import unittest
    unit_counts={'inspect_calls':0,'checker_steps':0}
    original_inspect=Checker.inspect
    def counted_inspect(self, event, certificate):
        previous=self.steps
        decision=original_inspect(self,event,certificate)
        unit_counts['inspect_calls']+=1
        unit_counts['checker_steps']+=self.steps-previous
        return decision
    Checker.inspect=counted_inspect
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    with (out/'unit-tests.txt').open('w') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    Checker.inspect=original_inspect
    if not result.wasSuccessful(): raise AssertionError('unit tests failed')
    write_json(out/'unit-summary.json', {'tests':result.testsRun,'failures':len(result.failures),
                                       'errors':len(result.errors),'status':'PASS',**unit_counts})
    stages.append({'stage':'unit-tests','cpu_seconds':time.process_time()-unit_cpu,
                   'wall_seconds':time.perf_counter()-unit_wall})
    redundant=redundant_run(2,out/'redundant-predicate.json')
    totals={}
    for n in contract['object_counts']:
        value=exhaustive_run(n,out,stride=1)
        stages.append({'stage':f'exhaustive-{n}','cpu_seconds':value['cpu_seconds'],
                       'wall_seconds':value['wall_seconds'],'peak_rss_kib':value['peak_rss_kib']})
        for key,v in value['counts'].items(): totals[key]=totals.get(key,0)+v
    programs=json.loads((ROOT/'inputs/witness-programs.json').read_text())
    witnesses=[]
    for program in programs:
        answer=bfs(program)
        oracle=enumerated_oracle(program)
        if answer['status']=='VIOLATION' and (oracle['status'],oracle['trace']) != ('VIOLATION',answer['trace']):
            raise AssertionError('least trace disagrees with whole-path oracle')
        witnesses.append({'case':program['case'],'bfs':answer,'path_oracle':oracle})
    negative={'phase_erasure':bfs(programs[3],key_mode='erase-ready'),
              'ghost_epoch_retention':bfs(programs[4],cap=64,key_mode='retain-epoch'),
              'capacity_cutoff':bfs(programs[2],cap=1)}
    if negative['phase_erasure']['status']!='SAFE' or negative['ghost_epoch_retention']['status']!='UNKNOWN':
        raise AssertionError('witness negative controls did not discriminate')
    write_json(out/'witnesses.json',{'cases':witnesses,'negative_controls':negative})
    # Certificate size is a deterministic representation size, not a compression optimum.
    heap=tuple((1,1,(i+1)%128) for i in range(128)); roots=frozenset({0})
    event=(127,1,0,-1); cert=produce(heap,roots,initial_cache(heap,roots),event)
    encoded=(json.dumps(cert,separators=(',',':'))+'\n').encode('utf-8')
    (out/'certificate-128.json').write_bytes(encoded)
    checker=Checker(heap,roots)
    capacity={'objects':128,'decision':checker.inspect(event,cert),'utf8_bytes_with_newline':len(encoded),
              'obligations':len(cert['checks']),'checker_steps':checker.steps}
    if capacity['decision']!='DENY_UNSAFE': raise AssertionError('capacity fixture did not deny')
    write_json(out/'capacity.json',capacity)
    for binary in ('javac','java'):
        if shutil.which(binary) is None: raise RuntimeError('a local JDK is required; nothing is downloaded')
    with tempfile.TemporaryDirectory(prefix='initialization-classes-') as temporary:
        jvm=['-XX:ActiveProcessorCount=1','-XX:+UseSerialGC','-Xmx256m']
        compile_stats=measured_process(['javac', *['-J'+flag for flag in jvm], '-proc:none','-d',temporary,
                                         str(ROOT/'java/BenignGraphs.java')],30,out/'java-compile.txt')
        java_stats=measured_process(['java',*jvm,'-cp',temporary,'BenignGraphs'],30,out/'java-observations.jsonl')
    stages.extend([{'stage':'java-compile',**compile_stats},{'stage':'java-observe',**java_stats}])
    observations=[json.loads(line) for line in (out/'java-observations.jsonl').read_text().splitlines()]
    if [x['case'] for x in observations] != [f'J{i:02d}' for i in range(24)]:
        raise AssertionError('Java fixture inclusion changed')
    callback_invalid=0
    for obs in observations:
        if obs['input_valid'] != obs['valid']:
            raise AssertionError('a round trip changed the selected final invariant')
        if obs['constructors_during_read'] != 0:
            raise AssertionError('the owned Serializable constructor ran during read')
        if len(obs['callback_states']) != obs['callbacks']:
            raise AssertionError('callback snapshot count mismatch')
        for callback in obs['callback_states']:
            bh=tuple(tuple(r) for r in callback['heap']); br=frozenset(callback['roots'])
            okay, live, _=exact(bh,br)
            if okay != callback['valid'] or all(bh[i][0] for i in live) != callback['all_ready']:
                raise AssertionError('callback snapshot disagrees with dense oracle')
            callback_invalid += not okay
        truth,_,_=exact(tuple(tuple(r) for r in obs['heap']),frozenset(obs['roots']))
        if truth!=obs['valid']: raise AssertionError('Java snapshot policy disagrees with dense oracle')
        try:
            Checker(obs['heap'],obs['roots']); admitted=True
        except ValueError: admitted=False
        if admitted != truth: raise AssertionError('checker admission disagrees with Java snapshot')
    java_summary={'cases':len(observations),'valid_final_snapshots':sum(x['valid'] for x in observations),
        'invalid_final_snapshots':sum(not x['valid'] for x in observations),
        'callbacks':sum(x['callbacks'] for x in observations),
        'callbacks_with_nonready_reachable_objects':sum(x['incomplete_callbacks'] for x in observations),
        'cases_with_nonready_callback_observation':sum(x['incomplete_callbacks']>0 for x in observations),
        'max_objects':max(len(x['heap']) for x in observations),'snapshot_mismatches':0,
        'callback_snapshots':sum(x['callbacks'] for x in observations),
        'invalid_callback_snapshots':callback_invalid,
        'constructors_during_read':sum(x['constructors_during_read'] for x in observations),
        'round_trip_validity_changes':sum(x['input_valid']!=x['valid'] for x in observations),
        'interpretation':'passive owned round trips; no JVM monitor or constructor-history refinement'}
    write_json(out/'java-summary.json',java_summary)
    with (out/'summary.csv').open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['measure','value'])
        writer.writerows(sorted(totals.items()))
    children=resource.getrusage(resource.RUSAGE_CHILDREN)
    parent=resource.getrusage(resource.RUSAGE_SELF)
    elapsed={'cpu_seconds':time.process_time()-own_begin+children.ru_utime+children.ru_stime-
              children_begin.ru_utime-children_begin.ru_stime,'wall_seconds':time.perf_counter()-begin,
             'parent_peak_rss_kib':parent.ru_maxrss,'child_peak_rss_kib':children.ru_maxrss,
             'aggregate_rss_upper_kib':parent.ru_maxrss+children.ru_maxrss,
             'stages':stages,'workers':1,'scientific_status':'FINITE_CHECKED_NOT_RESEARCH_LOCKED',
             'semantic_transitions':totals['transitions']+redundant['counts']['transitions']+
                  sum(x['bfs']['transitions']+x['path_oracle']['transitions'] for x in witnesses)+
                  sum(x['transitions'] for x in negative.values()),
             'checker_steps_exhaustive':totals['checker_steps'],
             'checker_steps_unit':unit_counts['checker_steps'],
             'checker_steps_capacity':capacity['checker_steps'],
             'unit_inspect_calls':unit_counts['inspect_calls'],
             'limitations':'RSS is a Linux parent/child maximum sum, not a simultaneous profiler. '
                  'No performance comparison with a production JVM monitor. Unit work is included in CPU, '
                  'unit inspect calls are reported separately from exhaustive candidate transitions.'}
    write_json(out/'measurements.json',elapsed)
    if args.verify_against:
        matched=verify(args.verify_against.resolve(),out)
        write_json(out/'replay-verification.json',{'status':'MATCH','matched_files':matched,
                   'excluded_fields':sorted(MEASUREMENT_KEYS),'independent_review':False})
    print(json.dumps({'status':'PASS','totals':totals,'java':java_summary,'measured_cpu_seconds':elapsed['cpu_seconds']},indent=2))

if __name__=='__main__':
    try: main()
    except (OSError,ValueError,RuntimeError,AssertionError,subprocess.TimeoutExpired) as exc:
        print(f'FAILED/UNKNOWN: {exc}',file=sys.stderr)
        raise SystemExit(2)
