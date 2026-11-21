#!/usr/bin/env python3
"""Generate reproducible A9 MAC thesis figures from existing results CSVs.
Run from anywhere: python python/plot_report_figures.py
No existing figures are overwritten: outputs go to results/report_figures/.
"""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'results'
OUT = DATA / 'report_figures'
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 10, 'figure.dpi': 120, 'savefig.dpi': 300})

def read(name, required):
    path = DATA / name
    if not path.exists():
        raise FileNotFoundError(f'Missing source: {path}')
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not set(required).issubset(reader.fieldnames or []):
            raise ValueError(f'{name}: missing {set(required)-set(reader.fieldnames or [])}')
        rows = list(reader)
    if not rows:
        raise ValueError(f'Empty source: {path}')
    return rows

def save(fig, name):
    fig.savefig(OUT / (name+'.png'), dpi=300, bbox_inches='tight')
    fig.savefig(OUT / (name+'.pdf'), bbox_inches='tight')
    plt.close(fig)
    print('Saved:', OUT / (name+'.png'))

def f(row, key): return float(row[key])

bit = read('bitwidth_sweep.csv', ['name','input_width','input_frac','mae','rmse','max_error'])
frac = read('fractional_sweep.csv', ['name','input_width','input_frac','mae','rmse','max_error'])
syn = read('summary_p0_p1_p2.csv', ['config','mae','p0_cells','p1_cells','p2_cells','p0_ff','p1_ff','p2_ff','p0_latency_cycles','p1_latency_cycles','p2_latency_cycles'])
rnd = read('rounding_sweep.csv', ['rounding_mode','num_samples','mae','rmse'])
ovf = read('overflow_sweep.csv', ['experiment','mode','num_samples','mae'])
by_name = {r['name']: r for r in bit}
if set(by_name) != {r['config'] for r in syn}:
    raise ValueError('Bitwidth and synthesis configurations do not match')
for row in syn:
    if abs(f(row,'mae')-f(by_name[row['config']],'mae')) > 1e-10:
        raise ValueError(f"MAE mismatch for {row['config']}")

# 1: accuracy: combine three metrics and show precision ceiling
fig, ax = plt.subplots(figsize=(9,5.3))
x = np.arange(len(bit)); labels = [f"{r['name']}\n{r['input_width']}b/{r['input_frac']}f" for r in bit]
for key, lab, marker in [('mae','MAE','o'),('rmse','RMSE','s'),('max_error','Max absolute error','^')]:
    ax.plot(x, [f(r,key) for r in bit], marker=marker, linewidth=2, label=lab)
ax.set_xticks(x,labels); ax.set_ylabel('Absolute numerical error'); ax.set_xlabel('Input width / fractional bits')
ax.set_title('Fixed-point accuracy across C1–C5 (1000 samples, length 8)')
ax.grid(alpha=.25); ax.legend(); ax.set_ylim(bottom=0)
fig.text(.5,.015,'Source: results/bitwidth_sweep.csv | Output: 8-bit, frac=4; seed=42',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.04,1,1]); save(fig,'01_accuracy_bitwidth')

# 2: fractional accuracy + representable range (two panels)
fig,(a,b)=plt.subplots(1,2,figsize=(11.2,4.8))
fx=[int(r['input_frac']) for r in frac]
a.plot(fx,[f(r,'mae') for r in frac],marker='o',label='MAE',linewidth=2)
a.plot(fx,[f(r,'rmse') for r in frac],marker='s',label='RMSE',linewidth=2)
a.set(xlabel='Input fractional bits (8-bit signed)',ylabel='Absolute numerical error',title='Accuracy with fixed input width')
a.set_xticks(fx); a.set_ylim(bottom=0); a.grid(alpha=.25); a.legend()
mins=[-2**(8-1-p) for p in fx]; maxs=[(2**7-1)/2**p for p in fx]
b.plot(fx,maxs,marker='o',label='Maximum representable')
b.plot(fx,mins,marker='s',label='Minimum representable')
b.axhspan(-.75,.75,alpha=.1,label='Test input range ±0.75')
b.set(xlabel='Input fractional bits (8-bit signed)',ylabel='Real input value',title='Representable range shrinks')
b.set_xticks(fx); b.grid(alpha=.25); b.legend(fontsize=8)
fig.suptitle('Fractional-bit allocation: accuracy versus dynamic range')
fig.text(.5,.015,'Sources: results/fractional_sweep.csv; signed fixed-point range derived from input width/frac',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.04,1,.94]); save(fig,'02_fractional_precision_range')

# 3: hardware resources, P0/P1/P2, two panels
fig,(a,b)=plt.subplots(2,1,figsize=(10.2,8.3),sharex=True)
sx=np.arange(len(syn)); width=.25
for ax, suffix, ylabel in [(a,'cells','Generic logic cells'),(b,'ff','Flip-flops')]:
    for j,p in enumerate(('p0','p1','p2')):
        vals=[int(r[f'{p}_{suffix}']) for r in syn]
        ax.bar(sx+(j-1)*width,vals,width,label=p.upper())
    ax.set_ylabel(ylabel); ax.grid(axis='y',alpha=.2); ax.set_axisbelow(True)
a.legend(ncol=3); a.set_title('Yosys generic resource counts: P0, P1 and P2')
b.set_xticks(sx,[r['config'] for r in syn]); b.set_xlabel('Bit-width configuration')
fig.text(.5,.015,'Source: results/summary_p0_p1_p2.csv | Generic cells are not FPGA LUTs or ASIC area',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.035,1,1]); save(fig,'03_hardware_cost_p0_p1_p2')

# 4: pipeline tradeoff, FF delta vs P0 and latency
fig,(a,b)=plt.subplots(1,2,figsize=(11.4,4.8))
for p,marker in [('p1','o'),('p2','s')]:
    a.plot(sx,[int(r[f'{p}_ff'])-int(r['p0_ff']) for r in syn],marker=marker,linewidth=2,label=f'{p.upper()} − P0')
a.set_xticks(sx,[r['config'] for r in syn]); a.set(xlabel='Configuration',ylabel='Additional flip-flops',title='Register overhead relative to P0'); a.grid(alpha=.25); a.legend()
for p in ('p0','p1','p2'):
    vals=[int(r[f'{p}_latency_cycles']) for r in syn]
    b.plot(sx,vals,marker='o',label=p.upper())
b.set_xticks(sx,[r['config'] for r in syn]); b.set_yticks([1,2,3]); b.set_ylim(.6,3.4)
b.set(xlabel='Configuration',ylabel='Latency (cycles)',title='Functional pipeline latency'); b.grid(alpha=.25); b.legend()
fig.suptitle('Pipeline cost: more registers and longer latency (II = 1 in verified cases)')
fig.text(.5,.015,'Source: results/summary_p0_p1_p2.csv | Fmax not measured',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.04,1,.93]); save(fig,'04_pipeline_cost_breakdown')

# 5: error vs hardware, three architectures
fig,ax=plt.subplots(figsize=(9.3,5.8))
for p,marker in [('p0','o'),('p1','s'),('p2','^')]:
    xs=[int(r[f'{p}_cells']) for r in syn]
    ys=[f(r,'mae') for r in syn]
    ax.plot(xs,ys,marker=marker,linewidth=1.5,label=p.upper())
    for r,xv,yv in zip(syn,xs,ys):
        ax.annotate(r['config'],(xv,yv),xytext=(4,4),textcoords='offset points',fontsize=8)
ax.set(xlabel='Yosys generic logic cell count (lower is better)',ylabel='MAE (lower is better)',title='Accuracy–hardware tradeoff for P0/P1/P2')
ax.grid(alpha=.25); ax.legend()
fig.text(.5,.015,'Sources: results/bitwidth_sweep.csv + summary_p0_p1_p2.csv | Not a timing-aware Pareto plot',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.04,1,1]); save(fig,'05_accuracy_hardware_tradeoff')

# 6a rounding, same experiment (1000 samples per policy)
fig,ax=plt.subplots(figsize=(8.5,5))
rx=np.arange(len(rnd)); rw=.33
for off,key,lab in [(-rw/2,'mae','MAE'),(rw/2,'rmse','RMSE')]:
    bars=ax.bar(rx+off,[f(r,key) for r in rnd],rw,label=lab)
    ax.bar_label(bars,fmt='%.4f',padding=3,fontsize=9)
ax.set_xticks(rx,['Truncate' if r['rounding_mode']=='truncate' else 'Nearest (ties away)' for r in rnd]); ax.set_ylabel('Absolute numerical error')
ax.set_title('Rounding policy comparison (1000 samples each)'); ax.legend(); ax.grid(axis='y',alpha=.2); ax.set_axisbelow(True)
fig.text(.5,.015,'Source: results/rounding_sweep.csv | Same dataset and numeric configuration',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.04,1,1]); save(fig,'06a_rounding_comparison')

# 6b overflow: separate scenarios, clearly marked sample counts
experiments=list(dict.fromkeys(r['experiment'] for r in ovf))
fig,axes=plt.subplots(1,len(experiments),figsize=(14,4.8))
if len(experiments)==1: axes=[axes]
for ax,exp in zip(axes,experiments):
    group=[r for r in ovf if r['experiment']==exp]
    vals=[f(r,'mae') for r in group]
    xx=np.arange(len(group)); bars=ax.bar(xx,vals)
    ax.set_xticks(xx,[r['mode'].replace('saturate_each_step','sat. each step') for r in group],rotation=20,ha='right',fontsize=8)
    ax.set_title(exp.replace('_',' ').title() + f"\n(n={group[0]['num_samples']})")
    ax.set_ylabel('Scenario-specific MAE'); ax.grid(axis='y',alpha=.2); ax.set_axisbelow(True)
    for bar,val in zip(bars,vals):
        ax.annotate(f'{val:.3g}',(bar.get_x()+bar.get_width()/2,bar.get_height()),xytext=(0,4),textcoords='offset points',ha='center',fontsize=9)
fig.suptitle('Overflow policies: separate scenarios, NOT a general policy ranking')
fig.text(.5,.015,'Source: results/overflow_sweep.csv | Different scenarios and small sample sizes; do not compare across panels',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.05,1,.92]); save(fig,'06b_overflow_scenarios')
print('\nCompleted: 7 PNG + 7 PDF in', OUT)
