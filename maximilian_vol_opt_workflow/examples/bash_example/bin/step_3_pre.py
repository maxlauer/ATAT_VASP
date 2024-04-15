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

from preprocessing import read_out_prev_calculation, change_poscar_volume, preprocessing

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

    if not os.path.exists(path):
        os.makedirs(path)

    params, covariance = curve_fit(murnaghan, df.volume, df.energy, p0=inital_guess)    

    params = pd.Series(params, index = ['F0', 'V0', 'K0', 'K1'])
    covariance = np.array(covariance)

    params.to_pickle(f'{path}/params.pkl')
    with open(f'{path}/covariance.pkl', 'wb') as file:
        pickle.dump(covariance, file)
    
    return params.loc['V0']


def extract_initial_guess(inital_opt_path, data_file, bulk_mod_guess: float = 10.0, bulk_mod_der_guess: float = 4.5):
    """
    initial guess in the form F0 V0 K0 K1
    """

    F0_guess = read_out_prev_calculation(calc_dir   = inital_opt_path, 
                                         data_file  = data_file, 
                                         prop       = "e_tol")
    V0_guess = read_out_prev_calculation(calc_dir   = inital_opt_path, 
                                         data_file  = data_file, 
                                         prop       = "volume")

    intial_guess = [F0_guess, V0_guess, bulk_mod_guess, bulk_mod_der_guess]

    return intial_guess


def read_out_prev_calcs(calc_path, step_dirs, data_file, structure_file, vol_en_file, initial_guess=[]):
    '''
    Function that extractes the volume and the Contcar path of calculations performed in step_1
    path - path to overarching step_1 dir (not the "calculation" subdirectory)
    '''
    paths = [f"{calc_path}/{step}" for step in step_dirs]

    base = f"{paths[0]}/{structure_file}"
    
    if initial_guess == []:
        initial_guess = extract_initial_guess(f"{paths[0]}/data.csv", data_file)
    
    vol_en_df = pd.read_csv(f"{paths[1]}/{vol_en_file}")
    
    vol_min = fit_murnaghan(vol_en_df, initial_guess, paths[2])

    return base, vol_min


def prep_s3(calc_path, inp_dir, vasp_dirs, subdir, step_1_dir, step_2_dir, data_file, structure_file, vol_en_file, bulk_mod_g: float = 10.0, bulk_mod_der_g: float = 4.5, pretty=False):
    
    # set up
    step_dirs = [step_1_dir, step_2_dir, subdir]
    initial_guess = extract_initial_guess(f"{calc_path}/{step_1_dir}", data_file, bulk_mod_g, bulk_mod_der_g)
    
    # read out and fitting of murnaghan
    base, vol_min = read_out_prev_calcs(calc_path       = calc_path,
                                        step_dirs       = step_dirs,
                                        data_file       = data_file,
                                        structure_file  = structure_file,
                                        vol_en_file     = vol_en_file,
                                        initial_guess    = initial_guess)

    # LATER - code duplication with step 2 - look into putting it in preprocessing .. prolly not its good enough
    # create Poscar in the step_3 directory to change volume of
    calc_dir = os.path.join(calc_path, subdir)
    if not os.path.exists(calc_dir):
        os.makedirs(calc_dir)
    
    poscar = f"{calc_dir}/POSCAR"
    shutil.copyfile(base, poscar)
    change_poscar_volume(poscar_path    =poscar, 
                         volume         =vol_min)

    preprocessing(calc_path     = calc_path, 
                  inp_dir       = inp_dir, 
                  vasp_dirs     = vasp_dirs, 
                  poscar_path   = poscar, 
                  subdir        = subdir, 
                  pretty        = pretty
                  )
    
    os.remove(poscar)



def main():
    parser = argparse.ArgumentParser("Preprocessing Step 3 of the Volume Optimization Workflow")

    parser.add_argument('--calc_dir', dest='calc_dir',  
                        help='directory in which the calculations are performed')
    parser.add_argument('--step_dir', dest='step_dir', default='step_3',
                        help='name of the directory in which the calculation of the step is to be performed')
    parser.add_argument('--s1_dir', dest='s1_dir', default='step_1',
                        help='name of the directory containing the initial calculation')
    parser.add_argument('--s2_dir', dest='s2_dir', default='step_2',
                        help='name of the directory containing the second step calculation')
    
    parser.add_argument('--input', dest='input', default='input', 
                        help='The input_file directory')
    parser.add_argument('--vasp_dirs', dest='vasp_dirs', nargs=4, default=['incars', 'kpoints', 'poscars', 'potcars'],
                        help='List of names for the directories containing INCAR, KPOINTS, POSCAR and POTCAR Files (in that order)')
    
    # defaults depend on postprocessing
    parser.add_argument('--data_csv', dest='data_file', default='data.csv',
                        help='name of the csv file outputted by the postprocessing scripts. Defaults to data.csv')
    parser.add_argument('--relaxed_str', dest='relaxed_str', default='relaxed_str.vasp',
                        help='name of the relaxed structure written by the postprocessing scripts. Defaults to relaxed_str.vasp')
    parser.add_argument('--volume_energy_data', dest='vol_en_file', default='s2_volume_energy.csv',
                        help='name of the relaxed structure written by the postprocessing scripts. Defaults to s2_volume_energy.csv')
    
    parser.add_argument('--bulk_mod_guess', dest='bulk_mod_g', type=float, default=10.,
                        help='inital bulk modulus parameter value. Defaults to 10')
    parser.add_argument('--bulk_mod_derivative_guess', dest='bulk_mod_der_g', type=float, default=4.5,
                        help='inital bulk modulus derivative parameter value. Defaults to 4.5')
    parser.add_argument('--pretty_incar', dest='pretty', action='store_true',
                        help='Reproduce Incar supplied by the user. Default - Write Incar in pymatgen style as a simple listing of arguments')


    args = parser.parse_args()

    prep_s3(calc_path       = args.calc_dir,
            inp_dir         = args.input,
            vasp_dirs       = args.vasp_dirs,
            subdir          = args.step_dir, 
            step_1_dir      = args.s1_dir,
            step_2_dir      = args.s2_dir,
            data_file       = args.data_file,
            structure_file  = args.relaxed_str,
            vol_en_file     = args.vol_en_file,
            bulk_mod_g      = args.bulk_mod_g,
            bulk_mod_der_g  = args.bulk_mod_der_g,
            pretty          = args.pretty
            )

if __name__ == '__main__':
    main()
