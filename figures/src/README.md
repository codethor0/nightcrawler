# Rebuilding the figures

The figure source files are tracked alongside eleven PNG and SVG outputs.
Figures 01-03, 04A, and 07-10 use Graphviz DOT. Figures 04, 05, and 06 use Python sources.

Install Graphviz and the Python packages used by the figure scripts (`matplotlib`, `Pillow`, and `cairosvg`), then run:

```bash
python3 figures/src/build_all.py
```

Figure regeneration may produce byte differences across renderer/font/platform versions. The checked-in figures are the immutable illustrations used with the archived manuscript; inspect generated output before proposing replacement artwork.
