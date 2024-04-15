import os
import shutil
import sys
import argparse

from preprocessing import preprocessing


def main():
    parser = argparse.ArgumentParser("Preprocessing Step 1 of the Volume Optimization Workflow")


    parser.add_argument('--calc_dir', dest='calc_dir',
                        help='The Directory in which the Calculation is to be performed')
    parser.add_argument('--step_dir', dest='step_dir', default='step_1',
                        help='name of the directory in which the calculation of the step is to be performed')

    parser.add_argument('--vasp_dirs', dest='vasp_dirs', nargs=4, default=['incars', 'kpoints', 'poscars', 'potcars'],
                        help='List of names for the directories containing INCAR, KPOINTS, POSCAR and POTCAR Files (in that order)')
    parser.add_argument('-p', '--poscar_file', dest='poscar_file', 
                        help='The path to the POSCAR to be used in the calculation, relative to vasp_dir[2]')
    
    parser.add_argument('--input', dest='input', default='input', help='The input_file directory')
    parser.add_argument('--pretty_incar', dest='pretty', action='store_true',
                        help='Reproduce Incar supplied by the user. Default - Write Incar in pymatgen style as a simple listing of arguments')

    args = parser.parse_args()

    preprocessing(calc_path     = args.calc_dir, 
                  inp_dir       = args.input, 
                  vasp_dirs     = args.vasp_dirs, 
                  poscar_path   = args.poscar_file, 
                  subdir        = args.step_dir, 
                  pretty        = args.pretty
                  )


if __name__ == '__main__':
    main()
