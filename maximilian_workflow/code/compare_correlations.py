import os
import sys

import numpy as np

import argparse

import tools


def main():
    parser = argparse.ArgumentParser("SQS-Candidate Evaluator")

    parser.add_argument('-i', '--input', dest='input', default='input',
                        help='The path where the input files are stored/generated - Defaults to \'input\' ')
    
    parser.add_argument('--damping', dest='damping', default=2,
                        help='The value of the damping constant - Defaults to 2')
    parser.add_argument('--calc_path', dest='calc_path', default='calc',
                        help='The path of the directory where the calculations are performed')
    parser.add_argument('--lattice_file', dest='lat_file', default='lat.in',
                        help='Name of the lattice file - Defaults to \'lat.in\'')
    parser.add_argument('--candidate_file', dest='candidate_file', default='sqs.out',
                        help='File to which the sqs candidates are written - Defaults to \'sqs.out\'')
    parser.add_argument('--cluster_files', dest='clust_file', default='clusters.out',
                        help='File containing the clusters - Defaults to \'clusters.out\'')
    parser.add_argument('--random_correlation_file', dest='rcorr_file', default='tcorr_rnd.out',
                        help='File to which the random correlations are written - Defaults to \'tcorr_rnd.out\'')
    parser.add_argument('--sqs_correlation_file', dest='scorr_file', default='tcorr.out',
                        help='File to which the correlations are written - Defaults to \'tcorr.out\'')
    parser.add_argument('--error_file', dest='error_file', default='errors.out',
                        help='File to which the errors are written - Defaults to \'errors.out\'')

    global args
    args = parser.parse_args()


    for folder in sorted(os.listdir(args.calc_path)):
        calc_errors(calc_path       = f"{args.calc_path}/{folder}", 
                    output_path     = args.error_file, 
                    rcorr_file      = args.rcorr_file, 
                    scorr_file      = args.scorr_file,
                    lattice_file    = args.lat_file, 
                    cluster_file    = args.clust_file, 
                    damping         = float(args.damping)
                    )


def calc_errors(calc_path:str, output_path:str, rcorr_file:str, scorr_file:str, lattice_file:str, cluster_file:str, damping):
    # read in the pair correlations
    rcorr, num_sqs, num_clus = tools.read_out_corr_file( f"{calc_path}/{rcorr_file}" )
    scorr, _, _ = tools.read_out_corr_file( f"{calc_path}/{scorr_file}" )

    # read in the cluster information
    coordinate_system = tools.get_coordinate_system( f"{calc_path}/{lattice_file}" )
    clusters = tools.read_out_cluster_file( f"{calc_path}/{cluster_file}", coordinate_system )

    print(f"\nNumber of sqs: \t\t{num_sqs}")
    print(f"Number of clusters: \t{num_clus} (including the point cluster)\n")

    error_list = []
    num_backspace = 0

    output_file = open(f"{calc_path}/{output_path}", 'w')
    for i in range(num_sqs):
        if i > 0:
            num_backspace = int(np.floor(np.log10(i))+1)
        sys.stdout.write(f"{"\b"*num_backspace}{i+1}")
        sys.stdout.flush()
        
        error = np.sum([clusters[j].multiplicity/(clusters[j].num_nodes*clusters[j].mean_distance())**damping*abs(scorr[i,j]-rcorr[i,j]) for j in range(1, num_clus)]) #first cluster excluded since it is a point cluster
        error_list.append(error)
        output_file.write(str(error)+"\n")

    print(f" Error functions corresponding to the input SQS where saved to \'{output_path}\'.\n")
    return error_list


# This is needed to choose the relative or absolute best SQS with one argument:
def restricted_float(x):
    if float(x) < 0.0:
        raise argparse.ArgumentTypeError("%r smaller than zero. Check -h for explanation of usage."%(x,))
    return float(x)


if __name__ == '__main__':
    main()