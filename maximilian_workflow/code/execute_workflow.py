import os
import sys
import argparse
import shutil
import numpy as np

from pymatgen.core.structure import Structure


def main():
    parser = argparse.ArgumentParser("SQS-Workflow Wrapper")
    
    
    # script paths
    parser.add_argument('--bin', dest='bin_dir', 
                        help='relative or absolute path to the bin directory containing the scripts')
    
    parser.add_argument('--candidate_gen', dest='candidate_gen', default='generate_candidates.py',
                        help='file name candidate generation script')
    parser.add_argument('--correlation_gen', dest='correlation_gen', default='generate_correlations.py',
                        help='file name correlation generation script')
    parser.add_argument('--candidate_compare', dest='candidate_compare', default='compare_correlations.py',
                        help='file name candidate generation script')
    parser.add_argument('--select_best', dest='select_best', default='select_sym_best.py',
                        help='file name best sqs selection script')
    parser.add_argument('--output_gen', dest='output_gen', default='generate_output.py',
                        help='file name best output generation script')
    

    # general input
    parser.add_argument('-i', '--input', dest='input', default='input',
                            help='The path where the input files are stored/generated - Defaults to \'input\' ')
    
    # candidate generation
    parser.add_argument('-m', '--mode', dest='mode_var', default='unique',
                        help='The flag determining the mode in which the candidate generation operates to generate the candidates. Options: unique; all; unique')
    parser.add_argument('-lim', '--limited', dest='lim_bool', action='store_true',
                        help='Limit SQS candidate generation to x <= 0.5')
    parser.add_argument('-mix', '--mixing_sites', dest='mixing', nargs=2,
                        help='Alloying Sites (first argument) and the replacement element')
    parser.add_argument('--super_cell_long', nargs=9, dest='sc_matrix', default=[1,0,0,0,1,0,0,0,1],
                        help='Supercell matrix, defaults to None. If given takes precedent over -sc')
    parser.add_argument('--tolerance', dest='atol', default=1e-5,
                        help='Tolerance when checking symmetry, Defaults to 1e-5')
    
    #correlation generation
    parser.add_argument('-d', '--distance_file', dest='distance_file', default='distance.dat',
                        help='File containing the max-distances for the clusters. Path relative to input path. Defaults to distance.dat')

    # compare correlations
    parser.add_argument('--damping', dest='damping', default=2,
                        help='The value of the damping constant - Defaults to 2')

    # select best
    parser.add_argument('-b', '--num_best', dest='num_best', default=3,
                        help='Number of SQS selected - Defaults to 3')
    parser.add_argument('-w', '--write_unique', dest='write_unique', action='store_false',
                        help='saves the subset of sqs that are within the lowest errors and sym unique to \'\"calc_path\"/unique_\"candidate_file\"\' and \'\"calc_path\"/unique_\"error_file\"\'')
    parser.add_argument('--num_errors', dest='num_err', default=5,
                        help='Number of Errors considered when checking symmetry - Defaults to 3')
    
    # generate output
    parser.add_argument('-o', '--output_dir', dest='output_dir', default='output',
                        help='The path to the directory where the finished \'best_file\' will be printed')
    parser.add_argument('--perform_match', dest='match_bool', action='store_true',
                        help='Compare the best sqs of the most expansive cluster calc with lower ones to preferably pick those that are the best sqs for multiple cluster amounts')


    # general paths
    parser.add_argument('--path', dest='path', default='calc',
                        help='The path of the super-directory where the calculations were performed')
    
    parser.add_argument('--base_str', dest='base_path', default='base.vasp',
                        help='The path of the input structure, relative to --input - Defaults to \'base.vasp\'')
    parser.add_argument('--precision', dest='prec', default=7,
                        help='Precision for float comparison - Defaults to 7')
    parser.add_argument('--seed', dest='seed', default=None,
                        help='randomness seed. default taken from sys parameters')
    
    global args
    args = parser.parse_args()

    max_distances = read_in_max_distance(f"{args.input}/{args.distance_file}")

    if not os.path.exists(args.path):
        os.makedirs(args.path)

    candidate_gen()
    
    for distance in max_distances:
        calc_path = f"{args.path}/{args.path}_{"_".join(distance)}"
        shutil.copytree(f"{args.path}/tmp", calc_path)

        #generate correlations
        os.system(f"python {args.bin_dir}/{args.correlation_gen} --input {args.input} --max_distances {" ".join(distance)} --calc_path {calc_path}")

        #calculate the errors
        os.system(f"python {args.bin_dir}/{args.candidate_compare} --input {args.input} --damping {args.damping} --calc_path {calc_path}")

        # select the best sqs
        write_unique = ""
        if args.match_bool or args.write_unique:
            write_unique = " --write_unique "
        os.system(f"python {args.bin_dir}/{args.select_best} --input {args.input} --num_best {args.num_best}{write_unique}--num_errors {args.num_err} --calc_path {calc_path}")
        
    #remove temporary candidate creation dir
    shutil.rmtree(f"{args.path}/tmp")

    # writing the output
    match = ""
    if args.match_bool:
        match = " --perform_match "
    os.system(f"python {args.bin_dir}/{args.output_gen} --input {args.input} --num_best {args.num_best} --output_dir {args.output_dir}{match}--path {args.path}")
    
    


def candidate_gen():
    # generate the candidate structures in a temporary directory
    if not os.path.exists(f"{args.path}/tmp"):
        os.makedirs(f"{args.path}/tmp")

    # read out the supercell configurations
    supercell = np.array(args.sc_matrix, dtype='float64').reshape(3,3)

    mixing_nums = determine_mixing_nums(f"{args.input}/{args.base_path}", args.mixing, supercell, True)#args.lim_bool)

    for conc in range(mixing_nums + 1):
        os.system(f"python {args.bin_dir}/{args.candidate_gen} --input {args.input} --mode {args.mode_var} --concentration {conc} --mixing_sites {" ".join(args.mixing)} --super_cell_long {" ".join([str(comp) for comp in supercell.reshape(1,-1).tolist()[0]])} --calc_path {args.path}/tmp --tolerance {args.atol}")


def determine_mixing_nums(str_path, mixing_sites, supercell, lim_bool):
    structure = Structure.from_file(str_path)
    
    mix_num_uc = np.sum([el.symbol == mixing_sites[0] for el in structure.species])
    mix_num_sc = int(round(mix_num_uc * np.linalg.det(supercell),3))
    
    if lim_bool:
        mix_num_sc = int(mix_num_sc/2)

    return mix_num_sc
    

def read_in_max_distance(path):
    ret = []
    with open(path, 'r') as f:
        lines = f.readlines()
    ret = [[dist for dist in line.strip('\n').split()] for line in lines]
    return ret

if __name__ == '__main__':
    main()
