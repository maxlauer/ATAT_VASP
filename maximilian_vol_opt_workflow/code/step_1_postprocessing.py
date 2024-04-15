import argparse

from postprocessing import postprocessing

def main():
    parser = argparse.ArgumentParser("Postprocessing of the initial step for volume optimization")

    parser.add_argument('-r', '--root', dest='root', 
                        help='directory from which the slurm script is launched')
    parser.add_argument('-c', '--calc_path', dest='calc_path', 
                        help='path in which the calculation is performed')
    parser.add_argument('--slurm_id', dest='sid', 
                        help='Id of the slurm batch job')
    
    parser.add_argument('--vasp_log', dest='vasp_log', default='output.log',
                        help='name of file containing the vasp output. Defaults to output.log')
    parser.add_argument('--slurm_log', dest='slurm_log', default='slurm_log',
                        help='name of file containing the slurm output. Defaults to slurm_log and is joined with _--slurm_id.log')
    
    parser.add_argument('--data_out', dest='data_file', default='data.out',
                        help='name of the human inteded out file. Defaults to data.out')
    parser.add_argument('--data_csv', dest='data_csv', default='data.csv',
                        help='name of the csv file. Defaults to data.csv')
    parser.add_argument('--relaxed_str', dest='relaxed_str', default='relaxed_str.vasp',
                        help='name of the relaxed structure written. Defaults to relaxed_str.vasp')
    parser.add_argument('--volume_energy_data', dest='vol_en_file', default='s2_volume_energy.csv',
                        help='name of the relaxed structure written. Defaults to s2_volume_energy.csv')
    parser.add_argument('--failed', dest='failed', default='failed_runs.out',
                        help='file containing run paths that didn\'t converge. Defaults to failed_runs.out')
    
    
    args = parser.parse_args()

    postprocessing(root=args.root,
                   calc_path=args.calc_path,
                   vasp_log=args.vasp_log,
                   slurm_log=f"{args.slurm_log}_{args.sid}.out",
                   data_file=args.data_file,
                   data_csv=args.data_csv,
                   failed_file=args.failed
                   )


if __name__ == '__main__':
    main()