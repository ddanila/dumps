"""Export independent PROM lanes and quantify waveform evidence; no invented ISA."""
from pathlib import Path
import json,csv,math
HERE=Path(__file__).resolve().parent;NOKIA=HERE.parents[1];OUT=HERE/'results';OUT.mkdir(exist_ok=True)
lanes=[(p,(NOKIA/'data-modem-2400-2400/microcode-810237c-810240c'/f'chip{p}-{label.lower()}.bin').read_bytes()) for p,label in [(10,'810237C'),(11,'810238C'),(17,'810239C'),(18,'810240C')]]
with (OUT/'prom-lanes.csv').open('w') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['address','chip10','chip11','chip17','chip18']);w.writerows([f'{a:03x}',*[f'{b[a]:02x}' for _,b in lanes]] for a in range(1024))
summary={'lane_order_note':'Columns are physical chip numbers, not established microinstruction bit order.','lanes':{str(p):{'unique_bytes':len(set(b)),'set_counts_by_bit_lsb_first':[sum((v>>i)&1 for v in b) for i in range(8)]} for p,b in lanes}}
b=(NOKIA/'data-modem-2400-2400/am27s31dc-prom/nokia-modem-am27s31dc.bin').read_bytes();samples=[x if x<128 else x-256 for x in b[:16]];expected=[round(127*math.sin(2*math.pi*i/16)) for i in range(16)]
summary['am27s31_first16']={'signed_samples':samples,'rounded_127_sine':expected,'exact_match':samples==expected,'note':'A lookup waveform, not proof of its frequency or connection to the DAC.'}
(OUT/'prom-analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
with (OUT/'am27s31.csv').open('w') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['address','hex','unsigned','signed']);w.writerows([f'{i:03x}',f'{v:02x}',v,v if v<128 else v-256] for i,v in enumerate(b))
try:
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(7,3));ax.plot(range(16),samples,'o-',label='PROM bytes interpreted as signed');ax.plot(range(16),expected,':',label='round(127 sin(2πn/16))');ax.set(xlabel='PROM address',ylabel='Signed value',title='Am27S31DC: first 16 bytes');ax.grid(alpha=.25);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'sine-table.svg');plt.close(fig)
except ImportError:print('Install matplotlib to regenerate optional SVG.')
print(json.dumps(summary['am27s31_first16']))
