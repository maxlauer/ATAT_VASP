import os
import shutil
import sys
import argparse

import pandas as pd

from preprocessing import prepare_calculation

def read_out_step_1(path):
    '''
    Function that extractes the volume and the Contcar path of calculations performed in step_1
    path - path to overarching step_1 dir (not the "calculation" subdirectory)
    '''
    lines = open(f"{path}/data.csv", 'r').readlines()
    
    for line in lines:
        values = line.strip('\n').split(',')
        if values[0] == 'Volume':
            print(values[1])
            return values[1], f"{path}/relaxed_str.vasp"
        
    return None, None

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


def set_up_environment(calc_path, init_dir, current_calc, inp_dir, vol_dev):
    '''
    Function to set up step 2 environment for Vasp Cacluations
     
    '''
    
    calc_dir = f"{calc_path}/{current_calc}/calculation"
    if not os.path.exists(calc_dir):
        print(calc_dir)
        os.makedirs(calc_dir)

    volume, poscar = read_out_step_1(f"{calc_path}/{init_dir}")


    if volume == None:
        print("Step 1 does not contain volume!!")
        sys.exit(1)

    potcar = f"{inp_dir}/potcars" 
    incar  = f"{inp_dir}/incars/INCAR_step_2"
    kpoint = f"{inp_dir}/kpoints/KPOINTS"

    prepare_calculation(calc_dir, poscar, potcar, incar, kpoint)

    change_poscar_volume(f"{calc_dir}/POSCAR", float(volume), int(vol_dev))
    
    
    



def main():
    parser = argparse.ArgumentParser("Preprocessing Step 1 of the Volume Optimization Workflow")

    parser.add_argument('--calc_dir', dest='calc_dir', 
                        help='directory in which the calculations are performed')
    parser.add_argument('--input_dir', dest='inp_dir', default='input', 
                        help='The input_file directory')
    parser.add_argument('--initial_calc', dest='init_dir', default='step_1',
                        help='name of the directory containing the initial structure')
    parser.add_argument('--current_dir', dest='step_2_dir', default='step_2',
                        help='name of the directory where step 2 is to be performed')
    parser.add_argument('--volume_deviation', dest='vol_dev', type=str,
                        help='volume deviation from the initial volume calculated in step 1, in percent')

    args = parser.parse_args()
    set_up_environment(args.calc_dir, args.init_dir, args.step_2_dir, args.inp_dir, args.vol_dev)


if __name__ == '__main__':

    main()
