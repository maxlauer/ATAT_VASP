import argparse
import os
import shutil
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import postprocessing as post

from step_3_preprocessing import murnaghan
# start out by checking if the calculation is converged - return sys.exit(1) if not -> afterok doesnt start
# the go ahead and write out the volume of step 1 into a volumes.out file
# write energy of step 1 into a energies.out file 
# write structure into a output/step_1.vasp file


# the path given is the path to the calculation environment - the output is to be printed in the parent dir

def plot_curve_fit(function, df_path, out_path):
    df = pd.read_csv(f'{df_path}')
    params = pd.read_pickle(f'{out_path}/params.pkl')
    plt.scatter(df.volume, df.energy, label='Data')

    x_smooth = np.linspace(np.min(df.volume), np.max(df.volume), 200)
    plt.plot(x_smooth, function(x_smooth, *params), label='Fitted curve', color='red')

    plt.xlabel('Volume / $10^{-30} m^3$')
    plt.ylabel('Energy / $eV$')
    plt.legend()
    plt.savefig(f'{out_path}/plot.png', dpi=200)
    plt.close()

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
    prev_path = "/".join(args.calc_path.split('/')[0:-2]) + '/step_2'
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

    #print the plots
    plot_curve_fit(murnaghan, f'{prev_path}/s2_volume_energy.csv', out_path)



if __name__ == '__main__':
    main()
