#!/bin/bash
OR=$(pwd)

s1_id=$(sbatch "$OR/bin/vol_opt_s1.job" $1 $2 | cut -d' ' -f4)
echo $s1_id

#s2_id=$(sbatch "$OR/bin/vol_opt_s2.job" "calc/$2" | cut -d' ' -f4)
s2_id=$(sbatch --dependency=afterok:$s1_id "$OR/bin/vol_opt_s2.job" $2 | cut -d' ' -f4)
echo $s2_id

s3_id=$(sbatch --dependency=afterok:$s2_id "$OR/bin/vol_opt_s3.job" $2 | cut -d' ' -f4)
echo $s3_id

exit
