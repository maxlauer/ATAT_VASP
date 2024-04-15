import io
import numpy as np

from pymatgen.io.atat import Mcsqs


def pmg_to_atat_str(structure, mixing=None, supercell=np.eye(3), species = [], direct=True):
    or_cell = (structure.lattice.matrix)
    if species == []:
        species = [el.symbol for el in structure.species]

    #convert original unit cell into coordinate_system
    if direct:
        cell=supercell
        coord_sys = np.matmul(or_cell, np.linalg.inv(supercell))
        coords = np.matmul(structure.frac_coords, supercell)
    else:
        cell=or_cell
        coord_sys = np.eye(3)
        coords = structure.cart_coords

    #write the coordinate system
    output = "\n".join([" ".join([f"{vec[i]:>10.7f}" for i in range(3)]) for vec in coord_sys])
    
    #write the unit cell
    output += "\n" + "\n".join([" ".join([f"{vec[i]:>10.7f}" for i in range(3)]) for vec in cell])
    
    #write the coordinates
    output += "\n" + "\n".join([" ".join([f"{pos[i]:>10.7f}" for i in range(3)] + [el]) for pos, el in zip(coords, species)])
    
    #if it's a lat.in then change the first mixing element to both in the lat.in
    if mixing != None:
        output = output.replace(mixing[0], f"{mixing[0]}, {mixing[1]}")
    
    return output


def sqs_list_to_pmg(sqs_list):
    ret = []
    for sqs in sqs_list:
        sqs_f = io.StringIO("\n".join(sqs))
        sqs_data = sqs_f.read()

        pmg_str = Mcsqs.structure_from_str(sqs_data)
        ret.append(pmg_str)
    return ret


def configs_to_atat_str(structure, configs, mixing_sites, supercell):
    
    output = ""

    for config in configs:
        species = adjust_chemical_species(
            structure   = structure, 
            config      = config, 
            mixing_site = mixing_sites[0])
        
        output += f"{pmg_to_atat_str(
            structure   = structure, 
            supercell   = supercell, 
            species     = species)}\nend\n\n"
    
    return output


def adjust_chemical_species(structure, config, mixing_site):
    
    symbols = [el.symbol for el in structure.species]
    positions = structure.indices_from_symbol(mixing_site)
    
    symbols[positions[0]:positions[-1] + 1] = config

    return symbols



def write_lat_list(path, sqs_list, supercell=np.eye(3)):
    output = ""
    for sqs in sqs_list:
        output += f"{pmg_to_atat_str(structure   = sqs, 
                                     supercell   = supercell)}\nend\n\n"
    with open(path, 'w') as f:
        f.write(output)



def read_in_lat_list(path):
    content = [line.rstrip() for line in open(path, 'r').readlines()]

    sqs_list = []
    single_sqs = []

    for line in content:

        if line == '':
            sqs_list.append(single_sqs)
            single_sqs = []
        
        elif line != 'end':
            single_sqs.append(line)

        
    return sqs_list