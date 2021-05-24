# FS_T1_WM_PIPELINE
Extracts image intensity statistics of white matter (WM) and gray matter (GM) across different regions using the freesurfer generated output and MNI152 templates.

---


## Setup

### Workflow 1: Singularity
1. Install [Singularity](https://sylabs.io/guides/3.7/user-guide/quick_start.html)
2. Clone this repository
```bash
git clone https://github.com/pndni/FS_T1_WM_PIPELINE.git
cd FS_T1_WM_PIPELINE
```
3. Build singularity container from docker [image](https://hub.docker.com/r/pndni/fs_t1_pipeline). Optional input `$TAG` for particular version (latest if left blank). 
```bash
chmod u+x build/*.sh
./build/build_singularity.sh ${TAG}
```


### Workflow 2: Manual Install


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

### Workflow 1
```bash
singularity run \
--bind "$indir":/mnt/indir:ro \
--bind "$outdir":/mnt/outdir \
--cleanenv \
fs_t1_pipeline_latest.simg <args>

```
### Workflow 2
```bash
./scripts/pipeline.sh <args> \ 
 -r $SUBJ_RECON_DIR -o $SUBJ_OUT_DIR \ 
 -l $FS_LICENSE [ -i $IMG ] [ -j $IMG2 ] [ -k $IMG3 ] [ -c ]
```
### Input Arguments

Run pipeline with (from project root):


`-r` `<INDIR>` - Path to input directory. This is the output of freesurfer's recon all \
(e.g. `recon-all-output/sub-12345`).


`-o` `<OUTDIR>` - Path to output directory \(e.g. `out/sub-12345`).


`-l` `<FREESURFER_LICENSE>` - Path to freesurfer lisence file (e.g. `./license.txt`).


`-i` `<IMG>` [OPTIONAL ARGUMENT]: Path to input T1 scan
 (e.g. `input/sub-12345/T1_sub-12345.nii.gz`). If left blank, defaults to `recon-all-output/sub-12345/mri/nu.mgz`. \
Note: Input image must be in the same space as the one used to run freesurfer (not necessarily same resolution and spacing). Output image statistics can be found under `out/sub-12345/stats`.

`-j` `<IMG2>` [OPTIONAL ARGUMENT]: Secondary image. Output of registration for `<$IMG>` is used to calculate statistics for `<$IMG2>`. `<$IMG2>` must be in the same space as `<$IMG>` (e.g. `input/sub-12345/T2_sub-12345.nii.gz`). Output image statistics can be found under `out/sub-12345/stats2`.

`-k` `<IMG3>` [OPTIONAL ARGUMENT]: Secondary image. Output of registration for `<$IMG>` is used to calculate statistics for `<$IMG3>`. `<$IMG3>` must be in the same space as `<$IMG>` (e.g. `input/sub-12345/DWI-FA_sub-12345.nii.gz`). Output image statistics can be found under `out/sub-12345/stats3`.

`-c` - Cleanup Flag [OPTIONAL ARGUMENT]: Deletes all generated output except the statistics directory/directories (`stats*`).

## Pipeline Summary
1) Run BET (if `-i <IMG>` is defined)
2) Linear registration: input image <> MNI152 (FLIRT)
3) Non-linear registration: input image <> MNI152 (FNIRT)
4) Transform MNI152 lobe mask, brain mask, cerebrum mask to native space (input image space)
5) Calculate intensity statistics of input image(s) masked by lobe mask and Desikan Killiany (DK) atlas (`out/sub-1234/stats`)


 ## Output

Sample output for a single subject: `out/sub-1234` \
Note: Check to make sure mask files in the `stats` directory overlay correctly onto the input image.
```bash
├── errorflag # Global Error log file (0 if ok)
├── logs # Log Files
│   ├── atlas_2_native_log_stderr.txt
│   ├── atlas_2_native_log_stdout.txt
│   ├── brainmask_2_native_log_stderr.txt
│   ├── brainmask_2_native_log_stdout.txt
│   ├── cerebrum_mask_2_native_log_stderr.txt
│   ├── cerebrum_mask_2_native_log_stdout.txt
│   ├── flirt_log_stderr.txt
│   ├── flirt_log_stdout.txt
│   ├── fnirt_log_stderr.txt
│   ├── fnirt_log_stdout.txt
│   ├── inv_warp_log_stderr.txt
│   ├── inv_warp_log_stdout.txt
│   ├── t1_2_ref_log_stderr.txt
│   └── t1_2_ref_log_stdout.txt
├── mri # Freesurfer input files
│   ├── brain.nii.gz
│   ├── DK_atlas.nii.gz
│   ├── GM_mask_ctx.nii.gz
│   ├── nu.nii.gz
│   ├── nu_to_MNI152_T1_2mm.log
│   └── WM_mask_all.nii.gz
├── pipeline.info # Pipeline version info
├── registration # FLIRT / FNIRT Registration files
│   ├── atlas_native.nii.gz
│   ├── brain_mask_native.nii.gz
│   ├── cerebrum_mask_native.nii.gz
│   ├── mni2struct_warp.nii.gz
│   ├── struct2mni_affine.mat
│   ├── struct2mni_warp.nii.gz
│   ├── T1_atlas_flirt.nii.gz
│   └── T1_atlas_fnirt.nii.gz
├── stats # Output stats for -i $IMG 
│   ├── ALL_stats_DK.csv
│   ├── ALL_stats_lobes.csv
│   ├── BrainMask.nii.gz
│   ├── CerebrumMask.nii.gz
│   ├── GM_stats_lobes.csv
│   ├── GrayMatterMask.nii.gz
│   ├── LabelMask_DK.nii.gz
│   ├── LabelMask_lobes.nii.gz
│   ├── WhiteMatterMask.nii.gz
│   └── WM_stats_lobes.csv
├── stats2 # Output stats for -j $IMG2 
│   ├── ALL_stats_DK.csv
│   ├── ALL_stats_lobes.csv
│   ├── BrainMask.nii.gz
│   ├── CerebrumMask.nii.gz
│   ├── GM_stats_lobes.csv
│   ├── GrayMatterMask.nii.gz
│   ├── LabelMask_DK.nii.gz
│   ├── LabelMask_lobes.nii.gz
│   ├── WhiteMatterMask.nii.gz
│   └── WM_stats_lobes.csv
└── stats3 # Output stats for -k $IMG3 
    ├── ALL_stats_DK.csv
    ├── ALL_stats_lobes.csv
    ├── BrainMask.nii.gz
    ├── CerebrumMask.nii.gz
    ├── GM_stats_lobes.csv
    ├── GrayMatterMask.nii.gz
    ├── LabelMask_DK.nii.gz
    ├── LabelMask_lobes.nii.gz
    ├── WhiteMatterMask.nii.gz
    └── WM_stats_lobes.csv
```

### Stats Files
- Columns repersent different statistical measures
- Rows represent different regions
- Last two rows represents the cerebrum and whole brain respectivelly. Suggested Normalization: Divide intensity statistics by the global whole-brain mean intensity (Last row in `../stats/ALL_stats_lobes.csv`)
---
- `ALL_stats_DK.csv` - Intensity statistics from regions defined in `LabelMask_DK.nii.gz`
- `ALL_stats_lobes.csv` - Intensity statistics from regions defined in `LabelMask_lobes.nii.gz`
- `BrainMask.nii.gz` - MNI152 brain mask in native space
- `CerebrumMask.nii.gz` - MNI152 cerebrum mask in native space (defined by labels 1-8 in ``LabelMask_lobes.nii.gz``)
- `GM_stats_lobes.csv` - Intensity statistics of GM regions defined by `LabelMask_lobes.nii.gz` and `GrayMatterMask.nii.gz`
- `GrayMatterMask.nii.gz` - GM tissue mask defined from `recon-dir/mri/ribbon.mgz`
- `LabelMask_DK.nii.gz` - Desikan Killany segmentation mask defined from `recon-dir/mri/aparc+aseg.mgz`
- `LabelMask_lobes.nii.gz` - MNI152 lobe masks transformed to native space
- `WhiteMatterMask.nii.gz` - WM tissue mask defined from `recon-dir/mri/aparc+aseg.mgz`
- `WM_stats_lobes.csv` - Intensity statistics of WM regions defined by `LabelMask_lobes.nii.gz` and `WhiteMatterMask.nii.gz`


### See `docs/FS_T1_PIPELINE.pdf` for more details.



### Lobe Mask
Label names for lobe mask (Lobe_Mask.nii.gz)

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


#### Pipeline originally tested with:
- Ubuntu 20.04.2 LTS
- FLIRT version 6.0.1
- Freesurfer 6.0.1
- Python 3.6.13 (packages list in requirements.txt)


# References
| Algorithm/software | Citation |
|--------------------|----------|
| parallel     | O. Tange (2011): GNU Parallel - The Command-Line Power Tool, ;login: The USENIX Magazine, February 2011:42-47. |
| FSL (ref 1)    | M.W. Woolrich, S. Jbabdi, B. Patenaude, M. Chappell, S. Makni, T. Behrens, C. Beckmann, M. Jenkinson, S.M. Smith. Bayesian analysis of neuroimaging data in FSL. NeuroImage, 45:S173-86, 2009 |
| FSL (ref 2)  | S.M. Smith, M. Jenkinson, M.W. Woolrich, C.F. Beckmann, T.E.J. Behrens, H. Johansen-Berg, P.R. Bannister, M. De Luca, I. Drobnjak, D.E. Flitney, R. Niazy, J. Saunders, J. Vickers, Y. Zhang, N. De Stefano, J.M. Brady, and P.M. Matthews. Advances in functional and structural MR image analysis and implementation as FSL. NeuroImage, 23(S1):208-19, 2004 |
| FSL (ref 3)  | M. Jenkinson, C.F. Beckmann, T.E. Behrens, M.W. Woolrich, S.M. Smith. FSL. NeuroImage, 62:782-90, 2012 |
| BET          | S.M. Smith. Fast robust automated brain extraction. Human Brain Mapping, 17(3):143-155, November 2002. |
| BET (skull)  | M. Jenkinson, M. Pechaud, and S. Smith. BET2: MR-based estimation of brain, skull and scalp surfaces. In Eleventh Annual Meeting of the Organization for Human Brain Mapping, 2005. |
| FLIRT (ref 1) | M. Jenkinson and S.M. Smith. A global optimisation method for robust affine registration of brain images. Medical Image Analysis, 5(2):143-156, 2001.  |
| FLIRT (ref 2) | M. Jenkinson, P.R. Bannister, J.M. Brady, and S.M. Smith. Improved optimisation for the robust and accurate linear registration and motion correction of brain images. NeuroImage, 17(2):825-841, 2002. | 
| FNIRT | Andersson JLR, Jenkinson M, Smith S (2010) Non-linear registration, aka spatial normalisation. FMRIB technical report TR07JA2 |
| FreeSurfer | http://surfer.nmr.mgh.harvard.edu/ (no overall paper) |
