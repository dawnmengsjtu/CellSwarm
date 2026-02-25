# CellSwarm v2 — GitHub Release Checklist

## Pre-release

- [ ] Fill in Lead Contact information (06_paper/sections/methods.tex)
- [ ] Fill in GitHub repository URL (06_paper/sections/methods.tex)
- [ ] Fill in Zenodo DOI (06_paper/sections/methods.tex)
- [ ] Choose and add License (MIT / Apache 2.0 / CC-BY-4.0)
- [ ] Verify no personal information leakage (emails, API keys, paths)
- [ ] Verify .gitignore excludes: _archive/, external/, .DS_Store, __pycache__
- [ ] Verify all figure CSVs are present in 05_figures/fig*/data/
- [ ] Verify README.md is up to date

## GitHub

- [ ] Create GitHub repository (public)
- [ ] Push code + knowledge bases + paper source
- [ ] Verify repo size is reasonable (< 100 MB without external/)
- [ ] Create GitHub Release tag `v1.0`

## Zenodo

- [ ] Create Zenodo deposit
- [ ] Upload `cellswarm-zenodo-simulation.tar.gz` (simulation output + analysis)
- [ ] Upload `cellswarm-zenodo-figures.tar.gz` (figure source data)
- [ ] Upload external reference data if permitted by license
- [ ] Set metadata (title, authors, description, keywords, license)
- [ ] Publish and obtain DOI
- [ ] Back-fill DOI into methods.tex and README.md

## Post-release

- [ ] Verify DOI resolves correctly
- [ ] Update GitHub README with Zenodo DOI badge
- [ ] Submit paper with final DOI references
