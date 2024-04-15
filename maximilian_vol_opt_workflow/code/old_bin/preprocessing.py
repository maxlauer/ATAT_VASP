import shutil
import os
import sys
import numpy as np

from ase.io import read,write

def write_potcar(potcar_dir, order, output_dir):
    potcar_order = ""
    for el in order:
        if not os.path.exists(f"{potcar_dir}/POTCAR_{el}"):
            print(f"{potcar_dir}/POTCAR_{el}")
            print("The Poscars contain elements not present in the POTCAR files provided. Please fix this before proceeding.")
            sys.exit(1)
        
        potcar_order += f"{potcar_dir}/POTCAR_{el} "
    
    os.system(f'cat {potcar_order} >> {output_dir}')

def prepare_calculation(calc_dir, poscar_path, potcar_path, incar_path, kpoint_path):
    #move over step_1 stuff
    
    def get_order(symobls):
        encountered = set()
        order = []
        for el in symobls:
            if el not in encountered:
                encountered.add(el)
                order.append(el)
        
        return order
    

    atm = read(poscar_path, format = 'vasp')
    order = get_order(atm.get_chemical_symbols())

    # move POSCAR
    shutil.copyfile(poscar_path, f"{calc_dir}/POSCAR")
    
    # move POTCAR
    write_potcar(potcar_path, order, f"{calc_dir}/POTCAR")

    # move KPOINTS
    shutil.copyfile(kpoint_path, f"{calc_dir}/KPOINTS")
    
    # move INCAR
    shutil.copyfile(incar_path, f"{calc_dir}/INCAR")

    # change directory into the calculation directory
    print(f"{os.getcwd()}/{calc_dir}", file=sys.stderr)
