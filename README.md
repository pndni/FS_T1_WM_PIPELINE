# FS_T1_WM_PIPELINE
Extracts image intensity statistics of white matter (WM) across different lobes using the freesurfer generated output.

---
## Requirements
Originally tested with:
- Ubuntu 20.04.2 LTS
- FLIRT version 6.0.1
- Freesurfer 6.0.1
- Python 3.6.13 (packages list in requirements.txt)

## Setup
1. Install [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation)
2. Install [FreeSurfer](http://www.freesurfer.net/fswiki/DownloadAndInstall)
3. Install [Python 3](https://www.liquidweb.com/kb/how-to-install-python-3-on-centos-7/) (example)
4. Clone this repository
```bash
git clone https://github.com/pndni/FS_T1_WM_PIPELINE.git
cd FS_T1_WM_PIPELINE
```
5. Install Python packages
```bash
pip3 install -r requirements.txt
```
6. Set `PIPELINE_HOME` environment variable
   to the location of the repository (using a full path).
```bash
export PIPELINE_HOME=${PWD}
```
## Usage

Run pipeline with (from project root):
```bash
./scripts/pipeline.sh <INDIR> <OUTDIR> <FREESURFER_LICENSE> <IMG_PATH>
```

`<INDIR>` - Path to input directory. This is the output of freesurfer's recon all \
(e.g. `recon-all-output/sub-12345`).


`<OUTDIR>` - Path to output directory. Overwrites anything already there \(e.g. `out/sub-12345`).


`<FREESURFER_LICENSE>` - Path to freesurfer lisence file (e.g. `./license.txt`).


`<IMG_PATH>` [OPTIONAL ARGUMENT]: Input scan
 (e.g. `input/sub-12345/sub-12345.nii.gz`). If left blank, defaults to `recon-all-output/sub-12345/mri/nu.mgz`. \
Note: Input image must be in the same space as the one used to run freesurfer (not necessarily same resolution and spacing).

## Pipeline Summary
1) Run BET (if <IMG_PATH> is not default)
2) Linear registration: input image <> mni152 (FLIRT)
3) Non-linear registration: input image <> mni152 (FNIRT)
4) Transform lobe mask, mni brain mask to native space (input image space)
5) Calculate intensity statistics of input image masked by lobe mask and brain mask (`out/sub-1234/stats/WM_stats.csv`)
6) Rescale input image intensity ([0, 1]) and calculate (`out/sub-1234/stats/WM_stats_norm.csv`)

 ## Output

Sample output for a single subject: `out/sub-1234` \
Note: Check to make sure mask files in the `stats` directory overlay correctly onto the input image.
``` bash
├── mri # Freesurfer input files
│   ├── brain_mask.nii.gz
│   ├── brain.nii.gz
│   ├── brain_skull.nii.gz
│   └── WM_mask_all.nii.gz
├── registration # FLIRT / FNIRT Registration files
│   ├── atlas_native.nii.gz
│   ├── brain_mask_native.nii.gz
│   ├── mni2struct_warp.nii.gz
│   ├── struct2mni_affine.mat
│   ├── struct2mni_warp.nii.gz
│   ├── T1_atlas_flirt.nii.gz
│   └── T1_atlas_fnirt.nii.gz
└── stats # Masks used for calculating stats
    ├── Brain_mask.nii.gz
    ├── cortex_mask.nii.gz
    ├── Lobe_mask.nii.gz
    ├── WhiteMatter_mask.nii.gz
    ├── WM_stats.csv # <-- Raw Image Statistics
    └── WM_stats_norm.csv # <-- Normalized ([0,1]) Image Statistics
```
### WM_stats
- Columns repersent different statistical measures
- Rows represent different regions / lobes
- Last row represents the entire brain / cortical region (labels 1-8 of lobe mask)


### Lobe Mask
Label names for lobe mask (Lobe_mask.nii.gz)

| Index | Region                | Hemisphere  |
|-------|-----------------------|-------------|
|  1.   | Frontal lobe          | right       |
|  2.   | Parietal lobe         | right       |
|  3.   | Temporal lobe         | right       |
|  4.   | Occipital lobe        | right       |
|  5.   | Frontal lobe          | left        |
|  6.   | Parietal lobe         | left        |
|  7.   | Temporal lobe         | left        |
|  8.   | Occipital lobe        | left        |
|  9.   | Cerebellum            | left        |
| 10.   | Sub-cortex            | left        |
| 11.   | Brainstem             | left        |
| 12.   | Cerebellum            | right       |
| 13.   | Sub-cortex            | right       |
| 14.   | Brainstem             | right       |
