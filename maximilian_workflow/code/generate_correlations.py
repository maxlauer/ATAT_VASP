import os
import shutil
import argparse

from tools import check_wdir


def main():
    parser = argparse.ArgumentParser("SQS-Candidate Generator")

    parser.add_argument('-i', '--input', dest='input', default='input',
                        help='The path where the input files are stored/generated - Defaults to \'input\' ')
    parser.add_argument('-d', '--max_distances', nargs=5, dest='distances',
                        help='max distance in clusters')
    
    parser.add_argument('--calc_path', dest='calc_path', default='calc',
                        help='The path of the directory where the calculations are performed')
    parser.add_argument('--lattice_file', dest='lat_file', default='lat.in',
                        help='Name of the lattice file - Defaults to \'lat.in\'')
    parser.add_argument('--candidate_file', dest='candidate_file', default='sqs.out',
                        help='File to which the sqs candidates are written - Defaults to \'sqs.out\'')
    parser.add_argument('--random_correlation_file', dest='rcorr_file', default='tcorr_rnd.out',
                        help='File to which the random correlations are written - Defaults to \'tcorr_rnd.out\'')
    parser.add_argument('--sqs_correlation_file', dest='scorr_file', default='tcorr.out',
                        help='File to which the correlations are written - Defaults to \'tcorr.out\'')
    
    global args
    args = parser.parse_args()

    with open(f"record.data", 'a') as f:
        f.write(f"{args.calc_path}: Distance Parameters are: {" ".join(args.distances)}")
        f.close()

    # set up working directory
    for folder in sorted(os.listdir(args.calc_path)):
        if not os.path.exists(f"{args.calc_path}/{folder}/{args.lat_file}"):
            shutil.copyfile(f"{args.input}/{args.lat_file}", f"{args.calc_path}/{folder}/{args.lat_file}")

        check_wdir(f"{args.calc_path}/{folder}", [args.lat_file, args.candidate_file])
        
        print(f"Generating correlations for {args.calc_path}/{folder}")
        generate_correlations(wdir          = f"{args.calc_path}/{folder}", 
                              max_distances = args.distances, 
                              candidates    = args.candidate_file, 
                              output        = args.rcorr_file, 
                              random_bool   = True)
        generate_correlations(wdir          = f"{args.calc_path}/{folder}", 
                              max_distances = args.distances, 
                              candidates    = args.candidate_file, 
                              output        = args.scorr_file, 
                              random_bool   = False)
        

def generate_correlations(wdir, max_distances, candidates, output, random_bool = True):
    src = os.getcwd()
    rand_flag = ''

    if random_bool:
        rand_flag = '-rnd'

    os.chdir(wdir)
    os.system(f'corrdump -noe -l {args.lat_file} -2 {max_distances[0]} -3 {max_distances[1]} -4 {max_distances[2]} -5 {max_distances[3]} -6 {max_distances[4]} -s {candidates} {rand_flag} > {output}')
    os.chdir(src)

    

        


if __name__ == '__main__':
    main()