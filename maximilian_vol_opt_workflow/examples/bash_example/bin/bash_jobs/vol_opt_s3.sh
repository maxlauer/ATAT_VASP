#!/bin/bash

#This will be a slurm script  - works so far but I will need to change it to a slurm file 

# Investigate how this works with environments .. prolly need to load my conda environments
# determine execution directory
OR=$(pwd)
R=$(dirname $OR)

#anyway - start by running the python preprocessing

calc_path=$(python /home/mlauer/Documents/work/sanna/volume_workflow/bin/step_3_preprocessing.py --calc_dir $1 2>&1 >/dev/null)
echo $calc_path
#cd $calc_path

## replacement for testing instead of actually running a calculation - this is simpler
output_path=$(dirname $calc_path)
step_2_dir=$(dirname $output_path)
subdir=${output_path#$step_2_dir/}

mv $calc_path $output_path"/calc_gen_pre"

example=$R"/example_calc/example/step_3"
cp -r $example"/calculation" $calc_path
cp $example"/slurm_log_"* $output_path

#then run the calculations
#srun /path/to/vasp/executable
#cd - >/dev/null

slurm_p=`echo $example"/slurm_log_"*".out"`
sid=`echo ${slurm_p#$example} | cut -d'_' -f3 | cut -d'.' -f1`
echo $sid

exit_code=$(python /home/mlauer/Documents/work/sanna/volume_workflow/bin/step_3_postprocessing.py --root $OR --calc_path $calc_path --slurm_id $sid)
echo $exit_code
# Then python postprocessing (with printing that the calcs are done and checking if they finished without error)
