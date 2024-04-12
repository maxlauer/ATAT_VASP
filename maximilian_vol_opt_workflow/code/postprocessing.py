import os
import shutil

from datetime import datetime, time

import pymatgen
from pymatgen.io.vasp.outputs import Outcar
from pymatgen.core.structure import Structure


def read_in_vasp_output(vasp_output_path):
    outcar = Outcar(f"{vasp_output_path}/OUTCAR")
    contcar = Structure.from_file(f"{vasp_output_path}/CONTCAR")
    
    return outcar, contcar

def read_in_meta_data(log_file_path):
    output_lines = open(log_file_path, 'r').readlines()
    try:
        vasp_version = output_lines[4].split()[0]
    except:
        print("There was a problem when reading out the vasp version")
        return None


    return vasp_version


def read_in_slurm_data(slurm_file_path):
    output_lines = open(slurm_file_path, 'r').readlines()
    year = output_lines[0].split()[-1]
    start = "-".join([year] + output_lines[0].split(" ")[3:6])
    end = "-".join([year] + output_lines[-1].split(" ")[3:6])
    
    start_time = datetime.strptime(start, '%Y-%d.-%b-%H:%M:%S')
    end_time = datetime.strptime(end, '%Y-%d.-%b-%H:%M:%S')
    difference = end_time - start_time
    
    return difference


def write_header(base_path, log_file, slurm_file, out_file_path):
    vasp_version = read_in_meta_data(f"{base_path}/{log_file}")
    time = read_in_slurm_data(f"slurm_logs/{slurm_file}")

    with open(out_file_path, 'w') as out_file:
        out_file.write("=============================\n")
        out_file.write(f"Calcultions performed\n")
        out_file.write(f"{"With:":<10}{vasp_version}\n")
        out_file.write(f"{"For:":<10}{time} hours\n")
        out_file.write("------------------------------\n")
        out_file.write(f"Output extracted with:\tPymatgen {pymatgen.core.__version__}\n")
        out_file.write("=============================\n\n")


def read_out_atom(outcar, contcar, out_file_path_h, out_file_path_csv):

    with open(out_file_path_h, 'a') as out_file:
        out_file.write(f"Total Energy: {outcar.final_energy} eV\n")
        out_file.write(f"Volume: {contcar.volume} A^3")

    with open(out_file_path_csv, 'a') as out_file:
        out_file.write(f"Total Energy, {outcar.final_energy}, eV\n")
        out_file.write(f"Volume, {contcar.volume}, A^3")

        


def check_convergence(vasp_output_path):
    is_converged = False
    with open(vasp_output_path, 'r') as file:
        for line in file.readlines():
            if line == " reached required accuracy - stopping structural energy minimisation\n":
                is_converged = True

    return is_converged


def read_out_structures(vasp_output_path, output_path):
    shutil.copyfile(f"{vasp_output_path}/CONTCAR", f"{output_path}/relaxed_str.vasp")
    shutil.copyfile(f"{vasp_output_path}/POSCAR", f"{output_path}/input_str.vasp")
    shutil.copyfile(f"{vasp_output_path}/XDATCAR", f"{output_path}/relax_traj.vasp")
