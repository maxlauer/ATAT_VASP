import os
import numpy as np

import bsym.interface.pymatgen as ipmg
from bsym.permutations import unique_permutations, flatten_list

from atat_lattice_file import pmg_to_atat_str


def generate_candidate_configurations(mix_str, num_sub, mixing_nums, mixing_sites, mode, atol=1e-5):
    
    
    site_distribution = { mixing_sites[0]: mixing_nums-num_sub, 
                         mixing_sites[1]: num_sub} # If I wanna change it up so it can be used for more than binary ..
    site_substitution_idx = list( mix_str.indices_from_symbol( mixing_sites[0] ) )
    numeric_site_distribution, numeric_site_mapping = ipmg.parse_site_distribution( site_distribution )
    
    if mode == 'unique':
        config_space = ipmg.configuration_space_from_structure( mix_str, subset=site_substitution_idx, atol=atol )
        unique_configurations = config_space.unique_configurations( numeric_site_distribution )
        configurations = [ [ mixing_sites[0] if mixing_sites[0] == numeric_site_mapping[element] else mixing_sites[1] for element in chem_config.tolist()] for chem_config in unique_configurations] # If I wanna change it up so it can be used for more than binary ..

    elif mode == 'all':
        s = flatten_list( [ [ key ] * site_distribution[ key ] for key in site_distribution ] ) 
        configurations = [ p for p in unique_permutations( s ) ]

    return configurations


def generate_base_lat_in(input_path, structure, mixing, supercell=np.eye(3)):
    #load a already existing lat.in file

    if not os.path.exists(f"{input_path}/lat.in"):
        lat_in = pmg_to_atat_str(structure, mixing, supercell)

        return lat_in
        
    else:
        pass
        #print("There already exists a lat.in file in the input - no new lat.in was generated. Please check that it is the correct lat.in for your calculation")
        

