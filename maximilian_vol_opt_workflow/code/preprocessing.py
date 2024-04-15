import shutil
import os
import sys

import numpy as np
import pandas as pd

from pymatgen.core.structure import Structure
from pymatgen.io.vasp import Incar



def change_poscar_volume(poscar_path, volume, vol_dev=0, change_name=False):
    '''
    read in the poscar file and change it's volume to volume * (1+vol_dev)
    '''
    with open(poscar_path, 'r') as poscar:
        lines = poscar.readlines()

    if change_name:
        lines[0] = f"{lines[0].strip('\n').strip(' ')} + {vol_dev} %\n"
    lines[1] = f"-{float(volume) + float(volume) * float(vol_dev)/100}\n"

    with open(poscar_path, 'w') as poscar:
        poscar.writelines(lines)


def write_potcar(potcar_dir, order, output_dir):
    potcar_order = ""
    for el in order:
        if not os.path.exists(f"{potcar_dir}/POTCAR_{el}"):
            print(f"{potcar_dir}/POTCAR_{el}")
            print("The Poscars contain elements not present in the POTCAR files provided. Please fix this before proceeding.")
            sys.exit(1)
        
        potcar_order += f"{potcar_dir}/POTCAR_{el} "
    
    os.system(f'cat {potcar_order} >> {output_dir}/POTCAR')


def change_up_incar_pretty(input_path, change_dir):
    """
    Applies the changes in change dir to the incar and returns a string to be written to a file
    Returns String
    """
    with open(input_path, 'r') as f:
        content = f.readlines()
    
    for i in range(len(content)):
        values = content[i].strip('\n').split('=')
        if values == []:
            continue
        
        elif values[0].strip() in change_dir.keys():
            values[-1] = change_dir[values[0].strip()]

            content[i] = "=  ".join(values) + "    # full relaxation of - forces, stress, position, cell, shape and volume\n"
    
    return "".join(content)


def set_up_directories(path):
    """
    // Return -> None
    // Input: 
        //path - path where the directory is to be set up 
    sets up the directory at path as the superdirectory of a particular vasp calculation
    a subdirectory called calculation, containing the actual calculation is created
    """

    calc_path = f"{path}/calculation"
    if not os.path.exists(calc_path):
        os.makedirs(calc_path)
    
    return calc_path


def prepare_vasp_calculation(calc_dir, input_files, pretty=False):
    
    def check_poscar(poscar_path):
        with open(poscar_path, 'r') as f:
            lines = f.readlines()
            scale = lines[1].rstrip()
            
            ret_bool = float(scale) > 0
                
        structure = Structure.from_file(filename=poscar_path)
        order = np.unique([ el.symbol for el in structure.species ])
        
        return ret_bool, order


    calc_path = set_up_directories(calc_dir)

    isif3, order = check_poscar(input_files["POSCAR"])

    for f_name, f_path in input_files.items():
        
        if f_name == "POTCAR":
            write_potcar(potcar_dir = f_path, 
                         order      = order, 
                         output_dir = calc_path
                         )
        
        elif f_name == "INCAR":
            incar = Incar().from_file(f_path)

            change_dict = {}
            if isif3:
                change_dict["ISIF"] = str(3)
                incar["ISIF"] = 3

            if pretty:
                incar_content = change_up_incar_pretty(f_path, change_dict)
            else:
                incar_content = incar.get_str(pretty=True)
            
            with open(f"{calc_path}/{f_name}", 'w') as out_f:
                out_f.write(incar_content)

        else:
            shutil.copyfile(f_path, f"{calc_path}/{f_name}")
        

def preprocessing(calc_path, inp_dir, vasp_dirs, poscar_path, subdir, pretty=False):
    """
    // input:
        // vasp_dirs - list of directories in input containing the vasp input
            //vasp_dirs[0] - INCAR
            //vasp_dirs[1] - KPOINTS
            //vasp_dirs[2] - POSCAR
            //vasp_dirs[3] - POTCAR
        // poscar_path - path containing the poscar file relative to vasp_dirs[2]
        // OR path absolute or relative to root to any POSCAR file to be used (e.g use of already relaxed files) 
        // !! Only uses the input path if poscar_path does not exist independently !!
    """
    def check_vasp_file(vasp_dir, vasp_file):
        # check if a general vasp_file exists or if path vasp_files exist.
        # If yes return the path, if no then raise error
        # step vasp_files take precedent
        for name in [f'{vasp_file}_step_1', f'{vasp_file}']:

            vasp_path = os.path.join(vasp_dir, name)
            if os.path.exists(vasp_path):
                return vasp_path
            
        raise ValueError(f"No {vasp_file} file in the speciefied directory ({vasp_dir}). Please provide one for the calculation to work")

    calc_dir = os.path.join(calc_path, subdir)

    calc_path = os.path.join(calc_dir, "calculation")
    if not os.path.exists(calc_path):
        os.makedirs(calc_path)

    # define input file paths
    if os.path.exists(poscar_path):
        poscar = poscar_path
    else:
        poscar = os.path.join(inp_dir, vasp_dirs[2], poscar_path)
    
    potcar = os.path.join(inp_dir, vasp_dirs[3])
    incar = check_vasp_file(os.path.join(inp_dir, vasp_dirs[0]), "INCAR")
    kpoints = check_vasp_file(os.path.join(inp_dir, vasp_dirs[1]), "KPOINTS")

    input_files = {"POSCAR":    poscar, 
                   "POTCAR":    potcar, 
                   "INCAR":     incar, 
                   "KPOINTS":   kpoints
                   }
    
    prepare_vasp_calculation(calc_dir       = calc_dir,
                             input_files    = input_files,
                             pretty         = pretty)
    
    # return the path to the directory of step_1
    print(calc_path, file=sys.stderr)


def read_out_prev_calculation(calc_dir, data_file, prop='volume'):

    data = pd.read_csv(f"{calc_dir}/{data_file}", index_col='property')
    print(data.columns)
    return data.loc[prop, 'value']

