"""Plot saved native results on common full-scale axes; no fitting or scoring."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parents[1]
r=json.loads((P/'artifacts/report.json').read_text())
names=list(r['systems']);colors=['#547083','#788e8d','#de9b46','#168b7a']
fig,axes=plt.subplots(1,2,figsize=(12,4.4))
for axis,key,title in zip(axes,['early_warning_recall','incident_precision'],['Early-warning recall','Notification precision']):
 values=[r['systems'][n][key] or 0 for n in names]
 axis.barh(names,values,color=colors)
 for y,value in enumerate(values):axis.text(min(value+.012,.95),y,f'{100*value:.1f}%',va='center',fontsize=9)
 axis.set(xlim=(0,1.07),xlabel='Fraction / common scale',title=title+' (higher is better)')
 axis.grid(axis='x',alpha=.15);axis.set_axisbelow(True)
fig.suptitle(f"{r['manifest']['version']} / {r['split']['test_runs']} predeclared fresh synthetic runs",fontsize=11)
fig.tight_layout();fig.savefig(P/'artifacts/benchmark.png',dpi=200);plt.close(fig)
print('Plotted frozen report; no model or test results changed.')
