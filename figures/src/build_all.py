#!/usr/bin/env python3
"""Rebuild all black-and-white figures. Does not silently substitute PNG artwork.
Requires Graphviz dot, matplotlib, Pillow and cairosvg (for the SVG merge)."""
from pathlib import Path
import subprocess
from PIL import Image, ImageOps
HERE=Path(__file__).resolve().parent
OUT=HERE.parent
for i in [1,2,3,7,8,9,10]:
    stem=f'fig{i:02}'
    src=HERE/(stem+'.dot')
    assert src.exists(),src
    subprocess.run(['dot','-Tpng','-Gdpi=180',str(src),'-o',str(OUT/(stem+'.png'))],check=True)
    subprocess.run(['dot','-Tsvg',str(src),'-o',str(OUT/(stem+'.svg'))],check=True)
subprocess.run(['dot','-Tpng','-Gdpi=180',str(HERE/'fig04a.dot'),'-o',str(OUT/'fig04a.png')],check=True)
subprocess.run(['dot','-Tsvg',str(HERE/'fig04a.dot'),'-o',str(OUT/'fig04a.svg')],check=True)
for i in [4,6]:
    stem=f'fig{i:02}'
    subprocess.run(['python3',str(HERE/(stem+'.py'))],cwd=OUT,check=True)
# Figure 5 is rebuilt from its black-and-white algorithmic illustration source.
subprocess.run(['python3',str(HERE/'fig05.py')],cwd=OUT,check=True)
print('Rebuilt 11 figures (1-10 plus 4A)')
