"""Compare two runtime profiles using the original evaluator and identical episodes."""
from pathlib import Path
from collections import defaultdict
import csv
import gzip
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time

root=Path('/kaggle/working');repo=root/'HA-VLN'
output=root/'havln-runtime/performance-bundle'
output.mkdir(exist_ok=True)
source=repo/'Data/HA-R2R/val_unseen/val_unseen.json.gz'
dataset=json.loads(gzip.decompress(source.read_bytes()))
by_scene=defaultdict(list)
for episode in dataset['episodes']:
    by_scene[episode['scene_id']].append(episode)
scenes=sorted(s for s,eps in by_scene.items() if len(eps)>=16)[:8]
assert len(scenes)==8
selected=[ep for scene in scenes for ep in sorted(by_scene[scene],key=lambda x:str(x['episode_id']))[:16]]
assert len(selected)==128
assert len({str(ep['episode_id']) for ep in selected})==128
dataset['episodes']=selected
path=repo/'Data/runtime-benchmark/val_unseen.json.gz'
path.parent.mkdir(exist_ok=True)
path.write_bytes(gzip.compress(json.dumps(dataset).encode()))
receipt={'episodes':128,'scenes':8,'episode_ids':[str(ep['episode_id']) for ep in selected],
         'dataset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
         'profiles':[], 'reference_navmesh_snapshot':str(repo/'Data/recompute_navmesh')}
(output/'dataset-receipt.json').write_text(json.dumps(receipt,indent=2))
profiles=[('reference_all_4',4,'all','0'),('optimized_scene_8',8,'scene','1')]
for name,count,scope,inference in profiles:
    folder=output/name;folder.mkdir(exist_ok=True)
    nav=folder/'navmesh'
    shutil.copytree(repo/'Data/recompute_navmesh',nav,copy_function=os.link)
    cmd=('source scripts/blackwell_env.sh && cd agent && '
         'python -u run.py --exp-config config/cma_pm_da_aug_tune.yaml --run-type eval '
         'MODEL.DEPTH_ENCODER.ddppo_checkpoint NONE VIDEO_OPTION \'[]\' '
         f'NUM_ENVIRONMENTS {count} '
         'TASK_CONFIG.DATASET.DATA_PATH ../Data/runtime-benchmark/val_unseen.json.gz '
         f'TASK_CONFIG.SIMULATOR.RECOMPUTE_NAVMESH_PATH {nav} '
         f'RESULTS_DIR {folder}/results')
    env=os.environ.copy();env.update(TORCH_HOME=str(root/'havln-runtime/torch-cache'),
                                    HAVLN_TEMPLATE_SCOPE=scope,HAVLN_FAST_INFERENCE=inference)
    (output/'status.json').write_text(json.dumps({'state':'running','profile':name,'started':time.time()},indent=2))
    monitor_file=open(folder/'gpu.csv','w')
    monitor=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,utilization.gpu,memory.used','--format=csv','-lms','1000'],stdout=monitor_file,stderr=subprocess.DEVNULL)
    log=open(folder/'run.log','w');begin=time.monotonic()
    proc=subprocess.Popen(['bash','-lc',cmd],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    print('PROFILE_STARTED',name,proc.pid,flush=True)
    try:
        code=proc.wait(timeout=360)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGTERM);code=124
    elapsed=time.monotonic()-begin
    monitor.terminate();monitor.wait();monitor_file.close();log.close()
    if code:
        (output/'status.json').write_text(json.dumps({'state':'failed','profile':name,'returncode':code},indent=2))
        raise RuntimeError(f'Original evaluator failed in {name}: status {code}')
    result=json.loads((folder/'results/stats_ckpt_0_val_unseen.json').read_text())
    util=[];memory=[]
    for row in csv.DictReader((folder/'gpu.csv').open()):
        row={k.strip():v.strip() for k,v in row.items()}
        util.append(float(row['utilization.gpu [%]'].split()[0]))
        memory.append(float(row['memory.used [MiB]'].split()[0]))
    entry={'name':name,'envs':count,'template_scope':scope,'inference_mode':inference=='1',
           'seconds':elapsed,'episodes_per_second':128/elapsed,'returncode':code,
           'gpu_utilization_mean':sum(util)/len(util) if util else None,
           'gpu_memory_peak_mib':max(memory) if memory else None,'metrics':result}
    entry['agent_steps']=round(result['steps_taken']*128)
    entry['agent_steps_per_second']=entry['agent_steps']/elapsed
    entry['gpu_utilization_peak']=max(util) if util else None
    receipt['profiles'].append(entry)
    (output/'comparison.json').write_text(json.dumps(receipt,indent=2))
    print('PROFILE_COMPLETED',json.dumps(entry),flush=True)
receipt['speedup']=receipt['profiles'][0]['seconds']/receipt['profiles'][1]['seconds']
receipt['agent_step_throughput_speedup']=receipt['profiles'][1]['agent_steps_per_second']/receipt['profiles'][0]['agent_steps_per_second']
(output/'comparison.json').write_text(json.dumps(receipt,indent=2))
(output/'status.json').write_text(json.dumps({'state':'complete','speedup':receipt['speedup']},indent=2))
print('BUNDLE_BENCHMARK_COMPLETE',receipt['speedup'],flush=True)
