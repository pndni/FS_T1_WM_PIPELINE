#!/bin/bash
#PBS -l walltime=24:00:00
#PBS -l nodes=1:ppn=32
#PBS -l mem=116g,vmem=116g
#PBS -e stderr
#PBS -o stdout
#PBS -m e

module load parallel

set -u
set -e
subjects=subjects_sample.txt
NTASKS_PER_NODE=128
start=$((PBS_ARRAYID * NTASKS_PER_NODE + 1))
num=32 # subjects to run concurrently

mkdir -p lists
subjfile=lists/subjects_s${start}_m${num}.txt

sed -n "$start,+$((NTASKS_PER_NODE - 1))p" < $subjects >> $subjfile

echo "start ${start} lines $((NTASKS_PER_NODE - 1)) task id ${PBS_ARRAYID}" | tee -a run_log.txt

parallel -j ${num} --joblog logs/parallel_s${start}_m${num}.log --wd $PWD ./run_subject.sh {} :::: $subjfile
