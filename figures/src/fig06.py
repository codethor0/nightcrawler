import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8.5,"mathtext.fontset":"dejavusans"})
fig, ax = plt.subplots(figsize=(7.2,3.3))
ax.set_xlim(-0.3,11.4); ax.set_ylim(-3.9,1.9); ax.axis("off")
ax.annotate("",xy=(11.3,0),xytext=(-0.2,0),arrowprops=dict(arrowstyle="-|>",lw=1.0,color="black"))
ax.text(11.3,-0.3,"time",ha="right",fontsize=8)
ev=[(0.4,r"$t_q^-$","earliest root\nissuance"),(2.1,r"$t_0$","termination\n(an interval)"),(3.7,r"$t_f$","fence\nconfirmed"),
    (5.4,"","actions,\nbarrier"),(7.0,r"$t_s$","re-observation\nsnapshot"),(8.5,r"$t_r$","receipt\nissued")]
for x,l,d in ev:
    ax.plot([x,x],[-0.12,0.12],color="black",lw=1.1)
    ax.text(x,0.22,l,ha="center",va="bottom",fontsize=9.5)
    ax.text(x,0.62,d,ha="center",va="bottom",fontsize=7.2)
ax.add_patch(plt.Rectangle((1.8,-0.06),0.6,0.12,fill=False,hatch="////",lw=0.6))
ax.add_patch(plt.Rectangle((4.3,-0.07),2.2,0.14,fill=True,color="0.85",lw=0))
def span(x0,x1,y,label,ls="-",lw=1.2):
    ax.annotate("",xy=(x1,y),xytext=(x0,y),arrowprops=dict(arrowstyle="<->",lw=lw,ls=ls,color="black",shrinkA=0,shrinkB=0))
    ax.plot([x0,x0],[y-0.12,y+0.12],color="black",lw=0.8); ax.plot([x1,x1],[y-0.12,y+0.12],color="black",lw=0.8)
    ax.text((x0+x1)/2,y-0.18,label,ha="center",va="top",fontsize=8)
span(0.4,7.0,-0.75,r"window for $U(q)$: created or modified in $[t_q^-, t_s]$ by $\mathrm{Auth}^*(q)$")
span(2.1,8.5,-1.55,r"exposure window $E_w = t_r - t_0$ (effects here are reported separately)")
span(8.5,9.9,-2.35,r"validity window $W$")
span(7.0,10.9,-3.15,r"liveness horizon $H$ measured from $t_s$",ls="--")
ax.plot([9.9,9.9],[-2.66,-3.15],ls=":",color="black",lw=0.9)
ax.text(4.2,-2.72,r"C8: $H \geq W + (t_r - t_s) + 2\epsilon_{clk}$",fontsize=8.2,va="center",ha="left")
ax.text(4.55,-0.33,"",fontsize=7)
plt.tight_layout(pad=0.2)
plt.savefig("fig06.png",dpi=220); plt.savefig("fig06.svg")
