import os
import shutil
import sys
import argparse

import numpy as np
import pandas as pd

from preprocessing import change_poscar_volume, read_out_prev_calculation, preprocessing


def prep_step_2(calc_path, inp_dir, vasp_dirs, subdir, step_1_dir, vol_dev, data_file, structure_file, pretty=False):
    def read_out_vol_dev(vol_dev):
        if np.abs(vol_dev) < 1:
            vol_dev = vol_dev * 100

        if vol_dev > 0:
            ret_dir = f'p_{int(np.abs(vol_dev))}'
        elif vol_dev < 0:
            ret_dir = f'm_{int(np.abs(vol_dev))}'
        else:
            ret_dir = 'n'

        return vol_dev, ret_dir
    
    volume = round(read_out_prev_calculation(f"{calc_path}/{step_1_dir}", data_file), 4)
    
    vol_dev, vol_dev_dir = read_out_vol_dev(vol_dev)

    subdir = os.path.join(subdir, vol_dev_dir)

    # create Poscar in the step_2 subdirectory to change volume of
    calc_dir = os.path.join(calc_path, subdir)
    if not os.path.exists(calc_dir):
        os.makedirs(calc_dir)
    
    poscar = f"{calc_dir}/POSCAR"
    shutil.copyfile(f"{calc_path}/{step_1_dir}/{structure_file}", poscar)
    change_poscar_volume(poscar_path= poscar, 
                         volume     = volume, 
                         vol_dev    = vol_dev, 
                         change_name= True)

    preprocessing(calc_path     = calc_path, 
                  inp_dir       = inp_dir, 
                  vasp_dirs     = vasp_dirs, 
                  poscar_path   = poscar, 
                  subdir        = subdir, 
                  pretty        = pretty
                  )
    
    os.remove(poscar)
    



def main():
    parser = argparse.ArgumentParser("Preprocessing Step 2 of the Volume Optimization Workflow")

    parser.add_argument('--calc_dir', dest='calc_dir', 
                        help='directory in which the calculations are performed')
    parser.add_argument('--step_dir', dest='step_dir', default='step_2',
                        help='name of the directory in which the calculation of the step is to be performed')
    parser.add_argument('--s1_dir', dest='init_dir', default='step_1',
                        help='name of the directory containing the initial structure')
    
    parser.add_argument('--input', dest='input', default='input', 
                        help='The input_file directory')
    parser.add_argument('--vasp_dirs', dest='vasp_dirs', nargs=4, default=['incars', 'kpoints', 'poscars', 'potcars'],
                        help='List of names for the directories containing INCAR, KPOINTS, POSCAR and POTCAR Files (in that order)')
    
    # defaults depend on postprocessing
    parser.add_argument('--data_csv', dest='data_file', default='data.csv',
                        help='name of the csv file outputted by the postprocessing scripts. Defaults to data.csv')
    parser.add_argument('--relaxed_str', dest='relaxed_str', default='relaxed_str.vasp',
                        help='name of the relaxed structure written by the postprocessing scripts. Defaults to relaxed_str.vasp')
    
    parser.add_argument('-v', '--volume_deviation', dest='vol_dev', type=float, 
                        help='volume deviation from the initial volume calculated in step 1, in percent (>1) or decimal')
    parser.add_argument('--pretty_incar', dest='pretty', action='store_true',
                        help='Reproduce Incar supplied by the user. Default - Write Incar in pymatgen style as a simple listing of arguments')


    args = parser.parse_args()
    
    #set_up_environment(args.calc_dir, args.init_dir, args.step_2_dir, args.inp_dir, args.vol_dev)
    prep_step_2(calc_path       = args.calc_dir, 
                inp_dir         = args.input, 
                vasp_dirs       = args.vasp_dirs, 
                subdir          = args.step_dir, 
                step_1_dir      = args.init_dir, 
                vol_dev         = args.vol_dev, 
                data_file       = args.data_file, 
                structure_file  = args.relaxed_str, 
                pretty          = args.pretty
                )

if __name__ == '__main__':
    main()
