# Paper Build Guide V5

`NO_REAL_EVIDENCE`

Preferred structural validation:

```bash
python3 -m certgen.audit.v5_audit --out docs/V5_FINAL_AUDIT.md --json-out data/results/v5_final_audit.json
```

Optional LaTeX build, if a CVPR style file is available locally:

```bash
cd paper
pdflatex main.tex
pdflatex supplement.tex
```

If LaTeX or the CVPR style file is unavailable, the V5 audit accepts structural validation instead.
