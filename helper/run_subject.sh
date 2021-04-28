#!/bin/bash

set -u
set -e
set -o pipefail

module load Singularity
subject="$1"


indir=indir_sample
outdir=outdir_sample
logdir=logs
mkdir -p $logdir

indir_sub=$indir/$subject
mkdir -p $indir_sub
outdir_sub=$outdir/$subject
mkdir -p $outdir_sub

#recon_dir=./recon-all-output
#tar -xvf $recon_dir/$subject/mri.tar -C $indir_sub

#cp license.txt $indir/license.txt
simg=./fs_t1_pipeline_latest.simg
echo $simg

singularity run \
--bind "$indir":/mnt/indir \
--bind "$outdir":/mnt/outdir \
--cleanenv \
$simg -r /mnt/indir/$subject \
-o /mnt/outdir/$subject \
-l /mnt/indir/license.txt -c \
> "$logdir"/"$subject"_stdout.log \
2> "$logdir"/"$subject"_stderr.log

# clean up
# rm -rf $indir_sub