import os
import io
import sys
import time

import argparse
import random
import pandas as pd
import numpy as np

from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.io.atat import Mcsqs

from atat_lattice_file import read_in_lat_list, write_lat_list


def main():
    parser = argparse.ArgumentParser("SQS-Selector")

    parser.add_argument('-i', '--input', dest='input', default='input',
                        help='The path where the input files are stored/generated - Defaults to \'input\' ')
    parser.add_argument('-b', '--num_best', dest='num_best', type=int, default=3,
                        help='Number of SQS selected - Defaults to 3')
    parser.add_argument('-w', '--write_unique', dest='write_unique', action='store_true',
                        help='saves the subset of sqs that are within the lowest errors and sym unique to \'\"calc_path\"/unique_\"candidate_file\"\' and \'\"calc_path\"/unique_\"error_file\"\'')

    parser.add_argument('--num_errors', dest='num_err', type=float, default=3,
                        help='Number of Errors considered when checking symmetry - Defaults to 3')
    parser.add_argument('--calc_path', dest='calc_path', default='calc',
                        help='The path of the directory where the calculations are performed')
    parser.add_argument('--best_file', dest='out_file', default='best_sqs.out',
                        help='The path of the directory where the calculations are performed')
    parser.add_argument('--candidate_file', dest='candidate_file', default='sqs.out',
                        help='File to which the sqs candidates are written - Defaults to \'sqs.out\'')
    parser.add_argument('--error_file', dest='error_file', default='errors.out',
                        help='File to which the errors are written - Defaults to \'errors.out\'')
    parser.add_argument('--precision', dest='prec', type=int, default=7,
                        help='Precision for float comparison - Defaults to 7')
    parser.add_argument('--supercell', dest='sc', nargs=9, default=[1, 0, 0, 0, 1, 0, 0, 0, 1],
                        help='Supercell array to be used as the unit cell in the lat.in representation (defaults to unit matrix)')
    parser.add_argument('--seed', dest='seed', default=None,
                        help='randomness seed. default taken from sys parameters')
    parser.add_argument('--verbose', dest='verbose', type=int, default=0,
                        help='Controls Verbosity- Defaults to \'0\'')

    global args
    args = parser.parse_args()

    # determine randomness seed
    if args.seed == None:
        seed = hash(str(time.time()) + str(sys.version))
    else:
        seed = args.seed

    global rng
    rng = random.Random(seed)

    #determine supercell
    supercell = np.array(args.sc).reshape(3,3)

    for folder in sorted(os.listdir(args.calc_path)):
        path = f"{args.calc_path}/{folder}"
        os.system(f'echo {seed} > {path}/seed.dat')

        sqs_dict = get_lowest_error_sqs(path=path, 
                                        sqs_file=args.candidate_file, 
                                        error_file=args.error_file, 
                                        precision=args.prec, 
                                        num_errors=args.num_err)
        
        unique_sqs_dict = determine_sym_unique(sqs_dict=sqs_dict)
        
        if args.write_unique:
            unique_sqs_list = []
            for sub_list in unique_sqs_dict.values():
                unique_sqs_list += sub_list
            
            write_lat_list(path     = f"{path}/unique_{args.candidate_file}", 
                           sqs_list = unique_sqs_list, 
                           supercell= supercell
                           )
            write_unique_errors(path        = f"{path}/unique_{args.error_file}", 
                                unique_sqs  = unique_sqs_dict
                                )

        best_sqs = select_best_sqs(sqs_dict = unique_sqs_dict,
                                   num_best = args.num_best,
                                   verbose  = args.verbose
                                   )

        write_lat_list(path      = f"{path}/{args.out_file}", 
                        sqs_list = best_sqs, 
                        supercell= supercell
                           )


def get_lowest_error_sqs(path, sqs_file, error_file, precision, num_errors):
    sqs_list = read_in_lat_list(f"{path}/{sqs_file}")

    errors = [round(float(value.strip()), int(precision)) for value in open(f"{path}/{error_file}", 'r').readlines()]
    unique_errors = pd.Series(sorted(pd.Series(errors).unique()))
    
    if num_errors > unique_errors.size:
        num_errors = int(unique_errors.size + 1)
    elif num_errors < 1:
        num_errors = int(unique_errors.size * num_errors)
    else:
        num_errors = int(num_errors)
    
    important_errors = unique_errors.iloc[0: num_errors].to_list()
    
    important_sqs = {error:[] for error in important_errors}
    
    for sqs, error in zip(sqs_list, errors):
        if round(float(error),int(precision)) in important_errors:
                important_sqs[error].append(sqs)

    return important_sqs


def determine_sym_unique(sqs_dict):
    """
    Input is a dictionary with the errors as keys and a list of all sqs with the error as the value, the function returns a dictionary of the same form, however sqs of the same symmetry are combined
    """
    # Initialize the StructureMatcher
    matcher = StructureMatcher()

    def check_sym(error_str, new_str):
        if error_str == []:
            error_str.append(new_str)
        
        else:
            for str in error_str:
                if matcher.fit(str,new_str):
                    return error_str
                else:
                    pass
            error_str.append(new_str)

        return error_str

    out = {} 
    for error, error_sqs in sqs_dict.items():
        sym_unique_sqs = []
        out[error] = []

        for sqs in error_sqs:

            sqs_f = io.StringIO("\n".join(sqs))
            sqs_data = sqs_f.read()

            pmg_str = Mcsqs.structure_from_str(sqs_data)
            sym_unique_sqs = check_sym(sym_unique_sqs, pmg_str)

        out[error] += (sym_unique_sqs) 
        
    return out


def select_best_sqs(sqs_dict, num_best, verbose):
    #writes best_sqs as a conc.in type file (for further refinement) and as Vasp POSCARS
    best_sqs = []
    target = num_best
    
    for error in sorted(sqs_dict.keys()):
        
        num_sqs = len(sqs_dict[error])
        
        if num_sqs > num_best:
            if num_sqs != num_best:
                if verbose > 0:
                    print(f"Too many structures with the lowest error.\n{num_best} were picked randomly")
            
                while len(best_sqs) < target:
                    best_sqs.append(rng.choice(sqs_dict[error]))
                break

        else:
            num_best = num_best - num_sqs
            best_sqs += sqs_dict[error]

    return best_sqs


def write_unique_errors(path, unique_sqs):
    print(path)
    output = ""
    for error in unique_sqs.keys():
        output += f"{error}\n" * len(unique_sqs[error])

    with open(path, 'w') as f:
        f.write(output)


if __name__ == '__main__':
    main()
