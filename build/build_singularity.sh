#!/bin/bash

set -eu

ver=$1

echo $PWD
tmpdir=$PWD/tmpdir
if [ -d $tmpdir ]; then
	rm -rf $tmpdir
fi
mkdir $tmpdir

dockerimg=pndni/fs_t1_pipeline:$ver

SINGULARITY_TMPDIR=$tmpdir
export SINGULARITY_TMPDIR

singularity build fs_t1_pipeline_$ver.simg docker://$dockerimg
rm -rf $SINGULARITY_TMPDIR
