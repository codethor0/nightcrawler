import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"mathtext.fontset":"dejavusans"})
fig, ax = plt.subplots(figsize=(7.2,4.1))
ax.set_xlim(0,10); ax.set_ylim(-0.35,5.4); ax.axis("off")
def box(x,y,w,h,ls="-",lw=1.1,r=0.12):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={r}",fill=False,ec="black",ls=ls,lw=lw))
box(0.1,0.25,6.05,4.95,ls=(0,(5,3)),lw=0.9)
ax.text(0.25,5.05,r"Artifacts observed in declared scope $S$ at re-observation time $t_s$",fontsize=8.3,va="top")
box(0.35,0.5,3.0,4.15,lw=1.2)
ax.text(0.5,4.5,r"$D_q^{\mathrm{verify}}$" "\n" r"some path from $q$" "\n" r"with no edge strictly" "\n" r"below $e_v$",fontsize=8.3,va="top")
box(0.6,0.75,2.45,1.35,lw=1.7)
ax.text(0.75,1.95,r"$D_q^{\mathrm{act}}$" "\n" r"every edge $\eta(e) \succeq e_a$",fontsize=8.3,va="top")
box(2.6,2.35,3.35,1.85,ls=(0,(3,2)),lw=1.2)
ax.text(2.75,4.08,r"$U(q)$" "\n" r"creator or modifier $\in \mathrm{Auth}^*(q)$" "\n" "per provider record;" "\n" "no edge evidence needed",fontsize=8.0,va="top")
def rbox(y,t,lw=1.1):
    box(6.6,y,3.3,1.05,lw=lw); ax.text(6.75,y+0.9,t,fontsize=8.0,va="top")
rbox(3.95,"Closure verification\n" r"all of $D^{\mathrm{verify}}_q \cup U(q)$ is checked" "\n" "for live paths (over-approximation)",lw=1.2)
rbox(2.4,"Quarantine or human approval\n" r"$(D^{\mathrm{verify}}_q \cup U(q)) \setminus D^{\mathrm{act}}_q$" "\n" "unresolved items listed on receipt")
rbox(0.75,"Automatic neutralization\n" r"only targets inside $D_q^{\mathrm{act}}$" "\n" "(under-approximation)",lw=1.7)
kw=dict(arrowstyle="-|>",lw=0.9,color="black",mutation_scale=9)
ax.annotate("",xy=(6.6,4.5),xytext=(3.35,4.5),arrowprops=kw)
ax.annotate("",xy=(6.6,2.95),xytext=(5.95,2.95),arrowprops=kw)
ax.annotate("",xy=(6.6,1.3),xytext=(3.05,1.3),arrowprops=kw)
ax.text(5.0,-0.2,r"Proposition 1:  $e_a \succeq e_v \;\Rightarrow\; D_q^{\mathrm{act}} \subseteq D_q^{\mathrm{verify}}$",fontsize=8.6,ha="center")
plt.tight_layout(pad=0.2)
plt.savefig("fig04.png",dpi=220); plt.savefig("fig04.svg")
