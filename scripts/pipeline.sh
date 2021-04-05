#!/bin/bash

# Writen by Andrei Mouraviev 
# Inspired by Steven Tilley (https://github.com/pndni/Charge_GM_WM_Properties_Pipeline/blob/master/scripts/pipeline.sh)
# Paus Lab

set -e  # exit on error
set -u  # exit on undefined variable
version=1.0.0-alpha

error() {
  >&2 echo $1
  exit 1
}

# Check FSLOUTPUTTYPE and store appropriate extension in "ext"
case "$FSLOUTPUTTYPE" in
    NIFTI_GZ)
	ext=".nii.gz"
	;;
    NIFTI)
	ext=".nii"
	;;
    *)
	error "Unsupported value for FSLOUTPUTTYPE: $FSLOUTPUTTYPE . Aborting"
	;;
esac

#if [ -e "$outdir" ]
#then
#    error "Output director already exists. Aborting"
#fi

selfhash=$(sha256sum $0)
fsversion=$(cat $FREESURFER_HOME/build-stamp.txt)
fslversion=$(cat $FSLDIR/etc/fslversion)

indir="${1}" # subject's recon all input
outdir="${2}" # output for subject
export FS_LICENSE="${3}"
T1_N3=${4:-"freesurfer_default"}
echo "T1 input ${T1_N3}"

if [ -d $outdir ]; then
    rm -rf $outdir
fi

mkdir -p $outdir/logs
mkdir -p $outdir/mri

PIPELINE_HOME=$PWD
if [ -z $PIPELINE_HOME ]; then
    export PIPELINE_HOME=$PWD
fi

# Reference Files
atlas="${PIPELINE_HOME}"/models/atlas_labels_ref.nii.gz
brainmask="${PIPELINE_HOME}"/models/icbm_mask_ref.nii.gz
mni_ref="${PIPELINE_HOME}"/models/MNI152_T1_2mm.nii.gz
mni_ref_brain="${PIPELINE_HOME}"/models/MNI152_T1_2mm_brain.nii.gz # reference for registration
fnirtconf="${PIPELINE_HOME}"/models/T1_2_MNI152_2mm.cnf

in_ext=".mgz"
out_ext=$ext

echo "CONVERTING ${in_ext} to ${out_ext}"
# T1 Used for calculating stats
if [ $T1_N3 == "freesurfer_default" ]; then
    T1_N3_mgz="${indir}"/mri/nu$in_ext # orig_nu.mgz
    T1_N3="${outdir}"/mri/nu$out_ext
    mri_convert $T1_N3_mgz $T1_N3
elif [ ! -f $T1_N3 ]; then
    error "T1 file does not exist: ${T1_N3}"
fi
# T1 Used for FLIRT
T1_brain_mgz="${indir}"/mri/brain$in_ext # orig_nu.mgz
T1_brain="${outdir}"/mri/brain$out_ext
mri_convert $T1_brain_mgz $T1_brain
# T1 Used for FNIRT
T1_mgz="${indir}"/mri/T1$in_ext # orig_nu.mgz
T1="${outdir}"/mri/T1$out_ext
mri_convert $T1_mgz $T1
# Brain skull-stripped
T1_brain_mgz="${indir}"/mri/brainmask$in_ext # orig_nu.mgz
T1_brain="${outdir}"/mri/brain$out_ext
mri_convert $T1_brain_mgz $T1_brain


# mri_binarize --i "${indir}"/mri/aparc+aseg.mgz --o "${outdir}"/mri/WM_mask_ctx.nii.gz  --ctx-wm
WM="${outdir}/mri/WM_mask_all${out_ext}"
mri_binarize --i "${indir}"/mri/aparc+aseg$in_ext --o $WM --all-wm


# REGISTRATION
reg_dir=$outdir/registration
mkdir -p $reg_dir

# linear registration
echo "FLIRT LINEAR REGISTRATION"
s2raff="${reg_dir}"/"struct2mni_affine.mat"
T1_atlas="${reg_dir}"/"T1_atlas_flirt${out_ext}"
echo flirt -ref "${mni_ref_brain}" -in "${T1_brain}" -out "${T1_atlas}" -omat "${s2raff}"
flirt -ref "${mni_ref_brain}" -in "${T1_brain}" -out "${T1_atlas}" -omat "${s2raff}"

# nonlinear registration
#     of original image to reference image
#     estimates bias field and nonlinear intensity mapping between images
#     Uses linear registration as initial transformation

echo "FNIRT NON-LINEAR REGISTRATION"
s2rwarp="${reg_dir}"/"struct2mni_warp${out_ext}"
echo fnirt --in="${T1}" --config="$fnirtconf" --ref="${mni_ref}" --aff="${s2raff}" --cout="${s2rwarp}"
fnirt --in="${T1}" --config="$fnirtconf" --ref="${mni_ref}" --aff="${s2raff}" --cout="${s2rwarp}"
# Test Warp
T1_atlas2="${reg_dir}"/"T1_atlas_fnirt${out_ext}"
applywarp --ref="${mni_ref}" --in="${T1}" --out="${T1_atlas2}" --warp="${s2rwarp}"

# Calculate inverse transformation
echo "CALCULATING INVERSE TRANSFORM"
r2swarp="${reg_dir}"/"mni2struct_warp${out_ext}"
invwarp --ref="${T1_N3}" --warp="$s2rwarp" --out="$r2swarp"


# apply inverse transformation to labels and brainmask
#    use nearest neighbor interpolation

echo "APPLYING INVERSE TRANSFORM"
atlas_native="${reg_dir}"/"atlas_native${out_ext}"
applywarp --ref="${T1_N3}" --in="${atlas}" --out="${atlas_native}" --warp="${r2swarp}" --interp=nn --datatype=int

brainmask_native="${reg_dir}"/"brain_mask_native${out_ext}"
applywarp --ref="${T1_N3}" --in="${brainmask}" --out="${brainmask_native}" --warp="${r2swarp}" --interp=nn --datatype=int

# Get Stats
stats_dir="${outdir}/stats"
python3.8 $PIPELINE_HOME/scripts/calc_stats.py -i $T1_N3 -WM $WM -LM $atlas_native -BM $brainmask_native -o $stats_dir