FROM centos:7.6.1810


RUN yum install -y epel-release && \
    yum install -y wget file bc tar gzip libquadmath which bzip2 libgomp tcsh perl zlib zlib-devel hostname && \
    yum groupinstall -y "Development Tools"

# FSL
RUN wget --output-document=/root/fslinstaller.py https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py && \
     python /root/fslinstaller.py -p -V 6.0.1 -d /opt/fsl && \
     rm /root/fslinstaller.py
ENV FSLDIR=/opt/fsl
ENV FSLOUTPUTTYPE="NIFTI_GZ"
ENV FSLMULTIFILEQUIT="TRUE"
ENV FSLTCLSH=/opt/fsl/bin/fsltclsh
ENV FSLWISH=/opt/fsl/bin/fslwish
ENV FSLLOCKDIR=""
ENV FSLMACHINELIST=""
ENV FSLREMOTECALL=""
ENV FSLGECUDAQ="cuda.q"
ENV PATH=/opt/fsl/bin:$PATH

# FreeSurfer
RUN wget --no-verbose --output-document=/root/freesurfer.tar.gz https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/6.0.1/freesurfer-Linux-centos6_x86_64-stable-pub-v6.0.1.tar.gz && \
    tar -C /opt -xzvf /root/freesurfer.tar.gz && \
    rm /root/freesurfer.tar.gz
ENV OS="Linux"
ENV FREESURFER_HOME=/opt/freesurfer
ENV FS_OVERRIDE=0
ENV FSFAST_HOME=/opt/freesurfer/fsfast
ENV FUNCTIONALS_DIR=/opt/freesurfer/sessions
ENV MINC_BIN_DIR=/opt/freesurfer/mni/bin
ENV MNI_DIR=/opt/freesurfer/mni
ENV MINC_LIB_DIR=/opt/freesurfer/mni/lib
ENV MNI_DATAPATH=/opt/freesurfer/mni/data
ENV LOCAL_DIR=/opt/freesurfer/local
ENV FSF_OUTPUT_FORMAT="nii.gz"
ENV MNI_PERL5LIB=/opt/freesurfer/mni/share/perl5
ENV PERL5LIB=${MNI_PERL5LIB}:$PERL5LIB
ENV PATH=${MINC_BIN_DIR}:$PATH
ENV PATH=/opt/freesurfer/fsfast/bin:/opt/freesurfer/bin:/opt/freesurfer/tktools:$PATH
ENV FIX_VERTEX_AREA=""

# Python
COPY requirements.txt /opt/pipeline/requirements.txt
RUN yum install -y python3 && \
    pip3 install -r /opt/pipeline/requirements.txt

RUN yum clean all

# Temorary directories
RUN mkdir -p /mnt/indir && \
    mkdir -p /mnt/outdir

# Project
COPY scripts /opt/pipeline/scripts/
COPY models /opt/pipeline/models/

ENV PIPELINE_HOME=/opt/pipeline

ENTRYPOINT ["/opt/pipeline/scripts/pipeline.sh"]

LABEL Maintainer="Andrei Mouraviev"
LABEL Version=alpha-1.0.2

