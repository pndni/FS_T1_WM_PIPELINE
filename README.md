# FS_T1_WM_PIPELINE
Extracts T1 WM intensity statistics using the freesurfer (v6.0.0) generated output.

---
## Requirements
Originally tested with:
- Ubuntu 20.04.2 LTS
- FLIRT version 6.0
- Python 3.8.5 (packages list in requirements.txt)

## Usage

Run `run.sh` through docker:
```bash
./scripts/pipeline.sh [INDIR] [OUTDIR] [FREESURFER_LICENSE] [T1_PATH]

```

`[INDIR]` - Path to input directory. This is the output of freesurfer's recon all
(e.g. `recon-all-output/sub-12345`).


`[OUTDIR]` - Path to output directory. Overwrites anything already there (e.g. `out/sub-12345`).


`[FREESURFER_LICENSE]` - Path to freesurfer lisence file (e.g. `./tmp/license.txt`).


`[T1_PATH]` - OPTIONAL ARGUMENT: Input T1 file (e.g. `data/sub-12345.nii.gz`). If left blank, defaults to `recon-all-output/sub-12345/mri/nu.mgz`.