import os
import shutil
import sys
import argparse

from preprocessing import prepare_calculation

def set_up_environment(wdir, inp_dir, poscar_file, poscar_dir):
    #poscar_dir = poscar_file.split('.')[0].replace('sqs', 'conc').replace("POSCAR", "sqs")

    calc_dir = f"{wdir}/{poscar_dir}/step_1/calculation"
    if not os.path.exists(calc_dir):
        os.makedirs(calc_dir)
    
    poscar = f"{inp_dir}/poscars/{poscar_file}"
    potcar = f"{inp_dir}/potcars"
    incar  = f"{inp_dir}/incars/INCAR_step_1"
    kpoint = f"{inp_dir}/kpoints/KPOINTS"

    prepare_calculation(calc_dir, poscar, potcar, incar, kpoint)



def main():
    parser = argparse.ArgumentParser("Preprocessing Step 1 of the Volume Optimization Workflow")

    parser.add_argument('--calc_dir', dest='calc_dir', default='calc', help='directory in which the calculations are performed')
    parser.add_argument('--input_dir', dest='inp_dir', default='input', help='The input_file directory')
    parser.add_argument('--poscar_file', dest='poscar_file', help='Basically the concentration which you want to calculate')
    parser.add_argument('--current_dir', dest='current_dir', help='The name of the directory to b e created')

    args = parser.parse_args()

    set_up_environment(args.calc_dir, args.inp_dir, args.poscar_file, args.current_dir)


if __name__ == '__main__':

    main()
