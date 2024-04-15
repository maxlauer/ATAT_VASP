import argparse
import os
import shutil
import sys

import postprocessing as post

# start out by checking if the calculation is converged - return sys.exit(1) if not -> afterok doesnt start
# the go ahead and write out the volume of step 1 into a volumes.out file
# write energy of step 1 into a energies.out file 
# write structure into a output/step_1.vasp file


# the path given is the path to the calculation environment - the output is to be printed in the parent dir

def main():
    parser = argparse.ArgumentParser("Postprocessing of the initial step for volume optimization")

    parser.add_argument('-r', '--root', dest='root', 
                        help='directory from which the slurm script is launched')
    parser.add_argument('-c', '--calc_path', dest='calc_path', 
                        help='path in which the calculation is performed')
    parser.add_argument('--slurm_id', dest='sid', 
                        help='Id of the slurm batch job')
    
    args = parser.parse_args()

    calc_path = args.calc_path
    out_path = "/".join(args.calc_path.split('/')[0:-1])
    root = args.root

    if not post.check_convergence(f"{calc_path}/output.log"):
        with open(f"{root}/failed_runs.out") as file:
            file.write(f"{calc_path}\n")
        sys.exit(1)

    # write out the meta data - how calcs were performed and data was extracted
    post.write_header(out_path, 'calculation/output.log', f'slurm_log_{args.sid}.out', f"{out_path}/data.out")

    # write out volume and total energy
    outcar, contcar = post.read_in_vasp_output(calc_path)
    post.read_out_atom(outcar, contcar, f"{out_path}/data.out", f"{out_path}/data.csv")

    #move INCAR
    post.read_out_structures(calc_path, out_path)



if __name__ == '__main__':
    main()
