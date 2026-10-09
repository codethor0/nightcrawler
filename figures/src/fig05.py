"""Black-and-white reconstruction of Figure 5: min cut vs constrained hitting set."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from pathlib import Path
OUT=Path(__file__).resolve().parent.parent
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':'black','axes.edgecolor':'black'})
fig=plt.figure(figsize=(7.2,5.7),facecolor='white')
gs=fig.add_gridspec(2,1,height_ratios=[1.06,1.12],hspace=.37)
a=fig.add_subplot(gs[0]);a.set_xlim(0,10);a.set_ylim(0,4.4);a.axis('off')
a.text(.1,4.22,'(a) Minimum source-to-effect cut',weight='bold',fontsize=12,va='top')
a.text(.1,3.8,'Special case: one intervention severs one element; additive costs.',fontsize=9.2,va='top')
pts={'s':(1.2,2.1),'a':(3.5,3.05),'b':(3.5,1.05),'c':(5.55,1.05),'f1':(7.4,3.05),'f2':(7.4,1.05),'t':(9.05,2.05)}
for k,(x,y) in pts.items():
    a.add_patch(Circle((x,y),.28,facecolor='white',edgecolor='black',lw=1.2))
    a.text(x,y,k if k not in {'f1','f2'} else '$f_'+k[-1]+'$',ha='center',va='center',fontsize=9)
def arr(u,v,lab=None,cut=False):
 x,y=pts[u];X,Y=pts[v]
 dx,dy=X-x,Y-y;d=(dx*dx+dy*dy)**.5;ux,uy=dx/d,dy/d
 a.add_patch(FancyArrowPatch((x+.29*ux,y+.29*uy),(X-.31*ux,Y-.31*uy),arrowstyle='-|>',mutation_scale=11,lw=1.6 if cut else 1,linestyle='--' if cut else '-',color='black'))
 if lab:a.text((x+X)/2,(y+Y)/2 + (.19 if cut else .13),lab,ha='center',va='bottom',fontsize=8.4)
arr('s','a','$\\infty$');arr('s','b','$\\infty$');arr('a','f1','cut $c=2$',True);arr('b','c','$c=5$');arr('c','f2','cut $c=1$',True);arr('f1','t','$\\infty$');arr('f2','t','$\\infty$')
a.text(.15,.18,'The cut separates residual seeds $R_q$ from prohibited effects $F^{-}$; total cost $2+1=3$.',fontsize=9.1,va='center')
b=fig.add_subplot(gs[1]);b.set_xlim(0,10);b.set_ylim(0,4.35);b.axis('off')
b.text(.1,4.25,'(b) Weighted hitting set with an operational invariant',weight='bold',fontsize=12,va='top')
b.text(.1,3.85,'An intervention may block several future-effect paths. Protected resources cannot be removed.',fontsize=9.0,va='top')
xs=[.45,5.45,6.6,7.75,8.9]
heads=['Action / cost','$p_1$','$p_2$','$p_3$','Allowed']
for x,h in zip(xs,heads):b.text(x,3.21,h,fontsize=9.2,weight='bold',ha='left' if x<1 else 'center')
b.plot([.4,9.58],[3.07,3.07],color='black',lw=1.1)
rows=[('m1: rotate shared credential  (3)',['X','X','X'],'YES'),('m2: disable schedule  (1)',['X','',''],'YES'),('m3: delete protected pipeline  (1)',['','X','X'],'NO')]
for i,(label,hits,allow) in enumerate(rows):
 y=2.62-i*.65
 b.text(.45,y,label,fontsize=8.75,va='center')
 for x,v in zip(xs[1:4],hits):b.text(x,y,v,fontsize=10,weight='bold',ha='center',va='center')
 b.text(8.9,y,allow,fontsize=8.8,weight='bold' if allow=='NO' else 'normal',ha='center',va='center')
 b.plot([.4,9.58],[y-.31,y-.31],color='black',lw=.4)
b.text(.45,.45,'Feasible optimum: {m1}, cost 3. Unconstrained {m2, m3}, cost 2, violates the invariant.',fontsize=9.0,va='center')
fig.subplots_adjust(left=.04,right=.985,top=.985,bottom=.035)
fig.savefig(OUT/'fig05.png',dpi=230,facecolor='white')
fig.savefig(OUT/'fig05.svg',facecolor='white')
plt.close(fig)
print('Figure5 rebuilt as vector and raster')
