#step 3 preprocessing has to take in the volume energy and fit it to murnaghan 
#prolly good to just plot in here as well and put it in the step 2 directory 
#then the postprocessing can just move the plot to the output directory together with the final volumes also in csv format
# apart from that it is just the typical procedure
import os
import shutil
import sys
import argparse

import pandas as pd
import numpy as np
import pickle

import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from preprocessing import prepare_calculation

def murnaghan(V, F0, V0, K0, K1):
    """
    Input:
        V - pd.Series - Volume - A^3
    ------------------------------------------
    Parameters
    ----------
    F0 - float - Energy at equilibrium Volume - eV
    V0 - float - equilibrium volume - A^3
    K0 - float - Bulk modulus - GPa
    K1 - float - pressure derivative of K0 - no dim

    ------------------------------------------
    Return - energy as function of volume - pd.Series - eV
    """
    e = 1.60217663 * 10 ** (-19)
    e_val = 1.60217663 #C divide Joule to get eV
    conversion_factor = e_val * 10**(-2)## G[Pa] (10**(9)) * [A^3](10**(-30)) * [1/e] 1/1.602 * 10**19

    return F0 + ( (K0 * V) / K1 * (((V0 / V) ** K1) / (K1 - 1) + 1) - (K0 * V0) / (K1 - 1) ) * conversion_factor

def fit_murnaghan(df, inital_guess, path):

    params, covariance = curve_fit(murnaghan, df.volume, df.energy, p0=inital_guess)    

    params = pd.Series(params, index = ['F0', 'V0', 'K0', 'K1'])
    covariance = np.array(covariance)

    params.to_pickle(f'{path}/params.pkl')
    with open(f'{path}/covariance.pkl', 'wb') as file:
        pickle.dump(covariance, file)
    
    return params.loc['V0']


def extract_initial_guess(path):

    def extract_run_1(path):
        ret = []

        with open(path, 'r') as file:
            lines = file.readlines()
        for line in lines:
            values = line.split(',')
            if values[0] in ["Total Energy", "Volume"]:
                ret.append(float(values[1]))
        return ret

    # for now hardcoded in 
    
    bulk_mod: float = 10.0
    bulk_mod_der: float = 4.5

    intial_guess = extract_run_1(path)
    intial_guess = intial_guess + [bulk_mod, bulk_mod_der]

    return intial_guess



def read_out_prev_calc(path_s1, path_s2, calc_path):
    '''
    Function that extractes the volume and the Contcar path of calculations performed in step_1
    path - path to overarching step_1 dir (not the "calculation" subdirectory)
    '''
    base = f"{path_s1}/relaxed_str.vasp"
    
    initial_guess = extract_initial_guess(f"{path_s1}/data.csv")
    vol_en_df = pd.read_csv(f"{path_s2}/s2_volume_energy.csv")
    
    vol_min = fit_murnaghan(vol_en_df, initial_guess, calc_path)

    return base, vol_min


def change_poscar_volume(poscar_path, volume, vol_dev):
    '''
    read in the poscar file and change it's volume
    '''
    with open(poscar_path, 'r') as poscar:
        lines = poscar.readlines()

    lines[0] = f"{lines[0].strip('\n').strip(' ')} + {vol_dev} %\n"
    lines[1] = f"-{float(volume) + float(volume) * int(vol_dev)/100}\n"

    with open(poscar_path, 'w') as poscar:
        poscar.writelines(lines)


def set_up_environment(wdir, inp_dir, init_dirs, curr_dir):
    calc_dir = f"{wdir}/{curr_dir}/calculation"
    if not os.path.exists(calc_dir):
        os.makedirs(calc_dir)
    
    r_dir = "/".join(calc_dir.split('/')[0:-1])

    poscar, vol_min = read_out_prev_calc(f"{wdir}/{init_dirs[0]}", f"{wdir}/{init_dirs[1]}", r_dir)
    potcar = f"{inp_dir}/potcars"
    incar  = f"{inp_dir}/incars/INCAR_step_3"
    kpoint = f"{inp_dir}/kpoints/KPOINTS"

    prepare_calculation(calc_dir, poscar, potcar, incar, kpoint)

    change_poscar_volume(f"{calc_dir}/POSCAR", vol_min, 0)


def main():
    parser = argparse.ArgumentParser("Preprocessing Step 1 of the Volume Optimization Workflow")

    parser.add_argument('--calc_dir', dest='calc_dir', help='directory in which the calculations are performed')
    parser.add_argument('--input_dir', dest='inp_dir', default='input', help='The input_file directory')
    parser.add_argument('--current_dir', dest='current_dir', default='step_3', help='The name of the directory to be created')
    parser.add_argument('--initial_calc', dest='init_dirs', nargs=2, default=['step_1', 'step_2'],
                        help='name of the directories containing the initial structure')


    args = parser.parse_args()

    set_up_environment(args.calc_dir, args.inp_dir, args.init_dirs, args.current_dir)
    sys.exit(0)


if __name__ == '__main__':

    main()
