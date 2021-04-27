#!/bin/bash

# Writen by Andrei Mouraviev 
# Inspired by Steven Tilley (https://github.com/pndni/Charge_GM_WM_Properties_Pipeline/blob/master/scripts/pipeline.sh)
# Paus Lab

set -e  # exit on error
set -u  # exit on undefined variable


error() {
  >&2 echo $1
  exit 1
}

check_file() {
    file=$1
    if [ ! -f $file ]; then
        error "ERROR: FILE DOES NOTES EXIST: ${file}"
    fi
}

check_dir() {
    file=$1
    if [ ! -d $file ]; then
        error "ERROR: DIRECTORY DOES NOTES EXIST: ${file}"
    fi
}

logcmd(){
    #https://stackoverflow.com/questions/692000/how-do-i-write-stderr-to-a-file-while-using-tee-with-a-pipe
    #thanks to lhunath
    mkdir -p logs
    local logbase
    logbase=logs/$1
    shift
    echo "Running: " "$@" " > >(tee ${logbase}_stdout.txt) 2> >(tee ${logbase}_stderr.txt >&2)"
    "$@" > >(tee ${logbase}_stdout.txt) 2> >(tee ${logbase}_stderr.txt >&2) || error "logcmd $1"
}

version=alpha-1.0.1

# Calculate and store hash of this file for logging and reproducibility
selfhash=$(sha256sum $0)
fsversion=$(cat $FREESURFER_HOME/build-stamp.txt)
fslversion=$(cat $FSLDIR/etc/fslversion)


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

#unset INDIR OUTDIR IMG FS_LICENSE
usage="Usage: pipeline.sh [ -r SUBJ_RECON_DIR ] [ -o SUBJ_OUT_DIR ] [ -l FS_LICENSE ] [ -i IMG ] [ -c CLEANUP_FLAG ]"

# DEFAULT VALUES
IMG="freesurfer_default"
CLEANUP_FLAG=0
while getopts r:o:l:i:c arg; do
    case "${arg}" in 
    r) INDIR="$OPTARG"
        ;;
    o) OUTDIR="$OPTARG"
        ;;
    l) export FS_LICENSE="$OPTARG"
        ;;
    i) IMG="$OPTARG"
        ;;
    c) CLEANUP_FLAG=1
        ;;
	?) >&2 echo $usage
	   exit 2
	   ;;
    esac
done

echo "Image input: ${IMG}"

if [ -d $OUTDIR ]; then
    error "ERROR: OUTDIR (-o) already exists ${OUTDIR}"
    #rm -rf $OUTDIR
fi

mkdir -p $OUTDIR
pushd "$OUTDIR" > /dev/null

# Check
check_dir $INDIR
check_dir $OUTDIR
check_file $FS_LICENSE

#PIPELINE_HOME=$PWD
#if [ -z "${PIPELINE_HOME}" ]; then
#    export PIPELINE_HOME=$PWD
#fi

# Reference Files
#brainmask="${PIPELINE_HOME}"/models/icbm_mask_ref.nii.gz # Used for nornalization constant
brainmask="${PIPELINE_HOME}"/models/MNI152_T1_2mm_bet_brain_mask.nii.gz # Used for nornalization constant
atlas="${PIPELINE_HOME}"/models/atlas_labels_ref.nii.gz
mni_ref="${PIPELINE_HOME}"/models/MNI152_T1_2mm.nii.gz
mni_ref_brain="${PIPELINE_HOME}"/models/MNI152_T1_2mm_brain.nii.gz # reference for registration
fnirtconf="${PIPELINE_HOME}"/models/T1_2_MNI152_2mm.cnf

check_file $atlas
check_file $brainmask
check_file $mni_ref
check_file $mni_ref_brain
check_file $fnirtconf

mri_dir=mri
mkdir -p $mri_dir

in_ext=".mgz"
out_ext=$ext


echo "CONVERTING ${in_ext} to ${out_ext}"
# T1 Used for calculating stats
if [ $IMG == "freesurfer_default" ]; then
    # Freesurfer IMG
    T1_N3_mgz="${INDIR}"/mri/nu$in_ext # orig_nu.mgz
    echo "Image not specified: Using default freesurfer (${T1_N3_mgz})"
    IMG="${mri_dir}"/nu$out_ext
    mri_convert $T1_N3_mgz $IMG
    # Brain skull-stripped - T1 Used for FLIRT
    T1_brain_mgz="${INDIR}"/mri/brainmask$in_ext # orig_nu.mgz
    IMG_brain="${mri_dir}"/brain$out_ext
    mri_convert $T1_brain_mgz $IMG_brain
elif [ -f $IMG ]; then
    bet_f=0.4  # parameter passed to FSL's  bet
    IMG_brain="${mri_dir}"/brain$out_ext
    logcmd bet_log bet "$IMG" "$IMG_brain" -f "$bet_f" -R -s -m
else
    error "IMG file does not exist: ${IMG}"
fi

# Double check that files and directories exist
check_file $IMG
check_file $IMG_brain


# mri_binarize --i "${INDIR}"/mri/aparc+aseg.mgz --o "${OUTDIR}"/mri/WM_mask_ctx.nii.gz  --ctx-wm
WM="${mri_dir}"/WM_mask_all"${out_ext}"
mri_binarize --i "${INDIR}"/mri/aparc+aseg"${in_ext}" --o $WM --all-wm
check_file $WM

GM_mgz="${INDIR}"/mri/ribbon$in_ext
GM="${mri_dir}"/GM_mask_ctx"${out_ext}"
#mri_binarize --i "${INDIR}"/mri/aparc+aseg"${in_ext}" --o $GM --gm
mri_binarize --i $GM_mgz --o $GM --match 3 42
check_file $GM


# REGISTRATION
reg_dir="${OUTDIR}/registration"
mkdir -p $reg_dir

# linear registration
echo "FLIRT LINEAR REGISTRATION"
s2raff="${reg_dir}"/"struct2mni_affine.mat"
T1_atlas="${reg_dir}"/"T1_atlas_flirt${out_ext}"
echo flirt -ref "${mni_ref_brain}" -in "${IMG_brain}" -out "${T1_atlas}" -omat "${s2raff}"
logcmd flirt_log flirt -ref "${mni_ref_brain}" -in "${IMG_brain}" -out "${T1_atlas}" -omat "${s2raff}"
check_file $T1_atlas
check_file $s2raff


# nonlinear registration
#     of original image to reference image
#     estimates bias field and nonlinear intensity mapping between images
#     Uses linear registration as initial transformation
echo "FNIRT NON-LINEAR REGISTRATION"
s2rwarp="${reg_dir}"/"struct2mni_warp${out_ext}"
echo fnirt --in="${IMG}" --config="${fnirtconf}" --ref="${mni_ref}" --aff="${s2raff}" --cout="${s2rwarp}"
logcmd fnirt_log fnirt --in="${IMG}" --config="${fnirtconf}" --ref="${mni_ref}" --aff="${s2raff}" --cout="${s2rwarp}"

# Warp from native to standard space to QC
T1_atlas2="${reg_dir}"/"T1_atlas_fnirt${out_ext}"
logcmd t1_2_ref_log applywarp --ref="${mni_ref}" --in="${IMG}" --out="${T1_atlas2}" --warp="${s2rwarp}"

# Calculate inverse transformation
echo "CALCULATING INVERSE TRANSFORM"
r2swarp="${reg_dir}"/"mni2struct_warp${out_ext}"
logcmd inv_warp_log invwarp --ref="${IMG}" --warp="$s2rwarp" --out="$r2swarp"


# apply inverse transformation to labels and brainmask
#    use nearest neighbor interpolation
echo "APPLYING INVERSE TRANSFORM"
atlas_native="${reg_dir}"/"atlas_native${out_ext}"
logcmd atlas_2_native_log applywarp --ref="${IMG}" --in="${atlas}" --out="${atlas_native}" --warp="${r2swarp}" --interp=nn --datatype=int

brainmask_native="${reg_dir}"/"brain_mask_native${out_ext}"
logcmd brainmask_2_native_log applywarp --ref="${IMG}" --in="${brainmask}" --out="${brainmask_native}" --warp="${r2swarp}" --interp=nn --datatype=int

# Get Stats
stats_dir="${OUTDIR}/stats"
python3 $PIPELINE_HOME/scripts/calc_stats.py -i $IMG -WM $WM -GM $GM -LM $atlas_native -BM $brainmask_native -o $stats_dir |& tee logs/stats_log

# Cleanup
ERROR=0
#WARNING=0

declare -a arr=("logs" "${stats_dir}" "${reg_dir}" "${mri_dir}")
for d in "${arr[@]}"
do
    if [ ! -d $d ]; then
        echo "ERROR: ${d} does not exist"
        ERROR=1
    fi

done

echo "CLEANUP_FLAG: ${CLEANUP_FLAG}"
if [ "${CLEANUP_FLAG}" == 1 ]; then
    echo "Cleaning workdir"
    rm -rf ${reg_dir}
    rm -rf ${mri_dir}
fi

echo $ERROR > errorflag
#echo $WARNING > warningflag

echo "selfhash: ${selfhash}" > pipeline.info
echo "pipeline version: ${version}" >> pipeline.info
echo "fsl version: ${fslversion}" >> pipeline.info
echo "freesurfer version: ${fsversion}" >> pipeline.info

popd > /dev/null

exit $ERROR