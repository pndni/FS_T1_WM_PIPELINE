#!/bin/bash

set -e
set -u

# run from repo root
# docker login --username=yourhubusername --password=yourpassword
ver=$1
#tmpdir=$(mktemp -d)

#git clone --branch $ver https://github.com/pndni/FS_T1_WM_PIPELINE.git $tmpdir
#pushd $tmpdir

#docker build -t pndni/fs_t1_pipeline:$ver .
#docker push pndni/fs_t1_pipeline:$ver


docker build -t pndni/fs_t1_pipeline .
docker tag pndni/fs_t1_pipeline pndni/fs_t1_pipeline:$ver
docker push pndni/fs_t1_pipeline