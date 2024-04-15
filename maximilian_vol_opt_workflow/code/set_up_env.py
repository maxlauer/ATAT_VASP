import os
import zipfile
import shutil

import numpy as np
import pandas as pd

import argparse

from pymatgen.io.vasp import Poscar
from pymatgen.io.atat import Mcsqs

from preprocessing import change_poscar_volume
from atat_lattice_file import read_in_lat_list, sqs_list_to_pmg

# THIS WHOLE THING HAS TO BE REWRITTEN

def main():

    parser = argparse.ArgumentParser()

    # if a folder is not listed in the volume file then they will be calculated with ISIF 3
    # otherwise the value from the file will be set as -volume in the poscar and ISIF NOT changed in preprocessing
    # either general INCAR or INCAR_step_1 will be used without change
    # if Volume is not supplied then INCAR or INCAR_step_1 will be used with a changed ISIF = 3 instead of the one supplied

    parser.add_argument('--input', dest='input', default='input', 
                        help='Directory containing incars,kpoints,potcars and poscars')
    parser.add_argument('--zipfile', dest='zipfile', default='lat_ins.zip',
                        help='zip-file containing directory \"finished\" with mcsqs files or poscar files')
    parser.add_argument('--mcsqs_file_name', dest='mcsqs_path', default='best_sqs.out',
                        help='Name of the mcsqs-files supplied. Defaults to \'best_sqs.out\'. If given as \'None\' only POSCAR files with .vasp ending are assumed')
    parser.add_argument('--calc_path', dest='calc_path', default='calc',
                        help='directory in which the calculations are performed')
    parser.add_argument('--volume_file', dest='vol_file', default='volume_file.csv',
                        help='Name of the file containing the volume information')
    
    parser.add_argument('--vasp_dirs', dest='vasp_dirs', nargs=4, default=['incars', 'kpoints', 'poscars', 'potcars'],
                        help='List of names for the directories containing INCAR, KPOINTS, POSCAR and POTCAR Files (in that order)')
     

    global args 
    args = parser.parse_args()

    # set up the general directories in the input directory
    set_up_input(args.input, args.vasp_dirs)

    # reads out the zip file and recreates it in the input/poscars directory
    read_out_zip_list(args.input, args.vasp_dirs[2], args.zipfile)

    # IF mcsqs files are supplied read out the list of mcsqs files and numerate the poscar files in the same directory as the lat in file
    # the file structure in input/poscars after this will reflect the structure of the calc environment 
    # with each POSCAR file being exchanged with a whole calculation environment
    convert_lat_ins(args.input, args.vasp_dirs[2], args.vol_file)


def set_up_input(input_path, vasp_dirs):
    """
    Return => None
    // Sets up the input directory (specified --input flag) with the --vasp_dir directories.
        // vasp_dirs[0] - INCAR - creates directory from which the INCARs for the Vasp Calculations are taken
        // vasp_dirs[1] - KPOINTS - creates directory from which the KPOINTS for the Vasp Calculations are taken
        // vasp_dirs[2] - POSCAR - creates directory from which the POSCARs for the Vasp Calculations are taken
            // If a mcsqs file is supplied then it will be unziped and the lattice files written out as poscars in this directory
        // vasp_dirs[3] - POTCAR - creates directory in which the POTCAR components are taken from
    // reads out lat_in zip file and changes the volume of the POSCARs
    """
    for directory in vasp_dirs:
        check_dir(f"{input_path}/{directory}")


def read_out_zip_list(input_path, poscar_path, zip_file):
    path = f"{input_path}/{zip_file}"
    output_path = f"{input_path}/{poscar_path}"
    tmp = f"{input_path}/tmp"

    with zipfile.ZipFile(path, 'r') as zip_ref:
        os.makedirs(tmp)
        zip_ref.extractall(tmp)

        for folder in sorted(os.listdir(tmp)):
            shutil.move(f'{tmp}/{folder}', f"{output_path}/{folder}")
        shutil.rmtree(tmp)


def convert_lat_ins(input_path, poscars_path, vol_file_path):
    volume_ser = pd.read_csv(f"{input_path}/{vol_file_path}", index_col='folder')
    
    for root, folders, files in os.walk(f"{input_path}/{poscars_path}"):

        for file in files:
            convert_sqs_list_poscars(root, file)
            

    for folder in sorted(volume_ser.index):
        poscar_files = [file for file in os.listdir(f"{input_path}/{poscars_path}/{folder}") if file.endswith('vasp') or file == "POSCAR"]
        
        for poscar in poscar_files:
            change_poscar_volume(poscar_path    = f"{input_path}/{poscars_path}/{folder}/{poscar}",
                                 volume         = float(volume_ser.loc[folder].item()),
                                 )


def convert_sqs_list_poscars(root, file):
    try:
        sqs_list = read_in_lat_list(f"{root}/{file}")
        str_list = sqs_list_to_pmg(sqs_list)

        number = 0
        for structure in str_list:

            while os.path.exists(f"{root}/POSCAR_{number}.vasp"):
                number += 1

            structure = structure.sort()
            structure.to(fmt="POSCAR", filename=f"{root}/POSCAR_{number}.vasp")
            number += 1

    except:
        pass


def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)







if __name__ == '__main__':
    input_path = "sqs_vol_opt" 
    os.chdir(input_path)
    main()    