import os
import argparse

import numpy as np

from pymatgen.core.structure import Structure

from atat_lattice_file import configs_to_atat_str
from config_generator import generate_base_lat_in, generate_candidate_configurations





def main():
    parser = argparse.ArgumentParser("SQS-Candidate Generator")

    parser.add_argument('-i', '--input', dest='input', default='input',
                        help='The path where the input files are stored/generated - Defaults to \'input\' ')
    parser.add_argument('-m', '--mode', dest='mode_var', default='unique',
                        help='The flag determining the mode in which the programm operates to generate the candidates. \
                            Options: unique - generate all symmetry unique structures using the bsym and pymatgen packages | default  \
                                        all - generate all structures using the bsym and pymatgen packages \
                                        gensqs - using the gensqs tool from the ATAT program')
    parser.add_argument('-c', '--concentration', dest='conc', type=float,
                        help='The concentration (<1) or amount of mixing-2 atoms')
    parser.add_argument('-mix', '--mixing_sites', dest='mixing', nargs=2, 
                        help='Alloying Sites (first argument) and the replacement element')
    parser.add_argument('-sc', '--super_cell', nargs=3, dest='sc_scaling', default=[1,1,1],
                        help='Scaling of the three cartesian basis vectors defaults to [1,1,1]')
    
    parser.add_argument('--base_str', dest='base_path', default='base.vasp',
                        help='The path of the input structure, relative to --input - Defaults to \'base.vasp\'')
    parser.add_argument('--calc_path', dest='calc_path', default='calc',
                        help='The path of the directory where the calculations are performed')
    parser.add_argument('--candidate_file', dest='candidate_file', default='sqs.out',
                        help='File to which the sqs candidates are written - Defaults to \'sqs.out\'')
    parser.add_argument('--lattice_file', dest='lat_file', default='lat.in',
                        help='Name of the lattice file - Defaults to \'lat.in\'')


    parser.add_argument('--super_cell_long', nargs=9, dest='sc_matrix', default=None,
                        help='Supercell matrix, defaults to None. If given takes precedent over -sc')
    parser.add_argument('--tolerance', dest='atol', type=float, default=1e-5,
                        help='Tolerance when checking symmetry, Defaults to 1e-5')
    

    global args
    args = parser.parse_args()


    # read out the supercell configurations
    if args.sc_matrix:
        supercell = np.array(args.sc_matrix, dtype='float64').reshape(3,3)
    else:
        supercell = np.eye(3)
        for ii in range(3):
            supercell[ii][ii] = args.sc_scaling[ii]


    # read in base_structure
    base_structure = read_in_pmg(f"{args.input}/{args.base_path}")
    # create supercell from base structure
    supercell_structure = base_structure.make_supercell(supercell, in_place=False)


    # determine the concentration
    mixing_nums = np.sum([ (el.symbol == args.mixing[0]) for el in supercell_structure.species ])

    if args.conc < 1:
        num_sub = args.conc * mixing_nums
        if round(num_sub % 1, 5) != 0:
            raise ValueError("Concentration doesn't lead to integer number of mixing sites")
        num_sub = int(num_sub)
    else:
        num_sub = int(args.conc)
            

    # first write the lat.in in the input directory, if it doesn't already exist
    lat_in = generate_base_lat_in(args.input, base_structure, args.mixing)
    if lat_in:
        with open( f'{args.input}/{args.lat_file}', 'w' ) as f:
            f.write( lat_in )


    # set up the calculation directory
    calc_dir = f'{args.calc_path}/sqs_{num_sub:0>{len(str(abs(mixing_nums)))}}'
    set_up_calc_directory( f'{args.calc_path}/sqs_{num_sub:0>{len(str(abs(mixing_nums)))}}' )


    # check the mode
    if args.mode_var == 'gensqs':
        print('NOT IMPLEMENTED YET')

    else:
        configs = generate_candidate_configurations(
            mix_str     = supercell_structure, 
            num_sub     = num_sub, 
            mixing_nums = mixing_nums, 
            mixing_sites= args.mixing, 
            mode        = args.mode_var, 
            atol        = args.atol
            )
        candidates = configs_to_atat_str(
            structure   = supercell_structure,
            configs     = configs,
            mixing_sites= args.mixing,
            supercell   = supercell
            )
        with open(f'{calc_dir}/{args.candidate_file}', 'w') as f:
            f.write(candidates)


def read_in_pmg(path):
    try:
        structure = Structure.from_file(path)
        return structure
    except:
        print(f"There were Problems when reading in the base structure {path}.")

    
def set_up_calc_directory(calc_path):
    if not os.path.exists(calc_path):
        os.makedirs(calc_path)



if __name__ == '__main__':
    main()