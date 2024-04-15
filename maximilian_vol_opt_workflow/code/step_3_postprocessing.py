import argparse
import os
import shutil
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from postprocessing import postprocessing

from step_3_preprocessing import murnaghan


def plot_curve_fit(function, df_path, out_path):
    df = pd.read_csv(f'{df_path}')
    params = pd.read_pickle(f'{out_path}/params.pkl')
    plt.scatter(df.volume, df.energy, label='Data')

    x_smooth = np.linspace(np.min(df.volume), np.max(df.volume), 200)
    plt.plot(x_smooth, function(x_smooth, *params), label='Fitted curve', color='red')

    plt.xlabel('Volume / $10^{-30} m^3$')
    plt.xlabel('Energy / $eV$')
    plt.legend()
    plt.savefig(f'{out_path}/plot.png', dpi=200)
    plt.close()


def main():
    parser = argparse.ArgumentParser("Postprocessing of the initial step for volume optimization")

    parser.add_argument('-r', '--root', dest='root', 
                        help='directory from which the slurm script is launched')
    parser.add_argument('-c', '--calc_path', dest='calc_path', 
                        help='path in which the calculation is performed')
    parser.add_argument('--s2_dir', dest='s2_dir', default='step_2',
                        help='name of the directory containing the second step calculation')
    
    parser.add_argument('--slurm_id', dest='sid', 
                        help='Id of the slurm batch job')
    parser.add_argument('--vasp_log', dest='vasp_log', default='output.log',
                        help='name of file containing the vasp output. Defaults to output.log')
    parser.add_argument('--slurm_log', dest='slurm_log', default='slurm_log',
                        help='name of file containing the slurm output. Defaults to slurm_log and is joined with _--slurm_id.log')
    
    parser.add_argument('--data_out', dest='data_file', default='data.out',
                        help='name of the human inteded out file. Defaults to data.out')
    parser.add_argument('--data_csv', dest='data_csv', default='data.csv',
                        help='name of the csv file. Defaults to data.csv')
    parser.add_argument('--relaxed_str', dest='relaxed_str', default='relaxed_str.vasp',
                        help='name of the relaxed structure written. Defaults to relaxed_str.vasp')
    parser.add_argument('--volume_energy_data', dest='vol_en_file', default='s2_volume_energy.csv',
                        help='name of the relaxed structure written. Defaults to s2_volume_energy.csv')
    parser.add_argument('--failed', dest='failed', default='failed_runs.out',
                        help='file containing run paths that didn\'t converge. Defaults to failed_runs.out')
    
    
    args = parser.parse_args()

    out_path = os.path.dirname(args.calc_path)
    outcar, contcar = postprocessing(root=args.root,
                                     calc_path=args.calc_path,
                                     vasp_log=args.vasp_log,
                                     slurm_log=f"{args.slurm_log}_{args.sid}.out",
                                     data_file=args.data_file,
                                     data_csv=args.data_csv,
                                     failed_file=args.failed
                                    )

    #print the plots
    calc_dir = os.path.dirname(out_path)
    plot_curve_fit(murnaghan, f'{calc_dir}/{args.s2_dir}/{args.vol_en_file}', out_path)


if __name__ == '__main__':
    main()