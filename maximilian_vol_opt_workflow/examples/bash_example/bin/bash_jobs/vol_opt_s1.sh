#!/bin/bash

#This will be a slurm script  - works so far but I will need to change it to a slurm file 

# Investigate how this works with environments .. prolly need to load my conda environments
# determine execution directory
OR=$(pwd)
R=$(dirname $OR)

if [ -n "$2" ] 
then
    output=$2
else
    output=`echo $1 | cut -d'.' -f1`
fi

#anyway - start by running the python preprocessing
#python path/to/file --poscar_file $1
calc_path=$(python /home/mlauer/Documents/work/sanna/volume_workflow/bin/step_1_preprocessing.py --calc_dir $output --poscar_file $1 2>&1 >/dev/null)

echo $calc_path
#cd $calc_path

## replacement for testing instead of actually running a calculation - this is simpler
output_path=$(dirname $calc_path)
echo $output_path

mv $calc_path $output_path"/calc_gen_pre"

cp -r $R"/example_calc/example/step_1/calculation" $calc_path
cp $R"/example_calc/example/step_1/slurm_log_$3.out" $R"/example_calc/example/step_1/slurm_log_$3.err" $output_path

#then run the calculations
#srun /path/to/vasp/executable
#cd - >/dev/null

exit_code=$(python /home/mlauer/Documents/work/sanna/volume_workflow/bin/step_1_postprocessing.py --root $OR --calc_path $calc_path --slurm_id $3)
echo $exit_code
# Then python postprocessing (with printing that the calcs are done and checking if they finished without error)
