import os
import sys 
import shutil
import time
import random
import argparse
import zipfile

import pandas as pd
import numpy as np

from atat_lattice_file import read_in_lat_list, write_lat_list, sqs_list_to_pmg
from tools import read_out_corr_file

from pymatgen.analysis.structure_matcher import StructureMatcher

'''
2 modes - either do a "meta" comparison - or just copy the best_sqs.out files to an temporary directory, 
zip them according to the specifications of the vol_op workflow and write to output directory
'''

def main():
    def eval_cluster_score(path):
        _, _, num_clus = read_out_corr_file(path)
        return num_clus


    parser = argparse.ArgumentParser("SQS-Selector")

    parser.add_argument('-i', '--input', dest='input', default='input',
                        help='The path where the input files are stored/generated - Defaults to \'input\' ')
    parser.add_argument('-b', '--num_best', dest='num_best', type=int, default=3,
                        help='Number of SQS selected - Defaults to 3')
    parser.add_argument('-o', '--output_dir', dest='output_dir', default='output',
                        help='The path to the directory where the finished \'best_file\' will be printed')
    parser.add_argument('-m', '--perform_match', dest='match_bool', action='store_true',
                        help='Compare the best sqs of the most expansive cluster calc with lower ones to preferably pick those that are the best sqs for multiple cluster amounts')

    parser.add_argument('--candidate_file', dest='candidate_file', default='sqs.out',
                        help='File to which the sqs candidates are written - Defaults to \'sqs.out\'')
    parser.add_argument('--path', dest='path', default='calc',
                        help='The path of the super-directory where the calculations were performed')
    parser.add_argument('--best_file', dest='out_file', default='best_sqs.out',
                        help='The path of the directory where the calculations are performed')
    parser.add_argument('-s', '--scorr', dest='sqs_correlation_file', type=str, default='tcorr.out',
                        help='Name of file containing sqs correlations. Defaults to \'tcorr_final.out\' if omitted.')
    
    parser.add_argument('--seed', dest='seed', default=None,
                        help='randomness seed. default taken from sys parameters')

    global args
    args = parser.parse_args()

    # determine randomness seed
    if args.seed == None:
        seed = hash(str(time.time()) + str(sys.version))
    else:
        seed = args.seed

    global rng
    rng = random.Random(seed)

    
    if not os.path.exists(f"{args.output_dir}/finished"):
        os.makedirs(f"{args.output_dir}/finished")

    if args.match_bool:
        folders = {folder: eval_cluster_score(f"{args.path}/{folder}/{os.listdir(f"{args.path}/{folder}")[0]}/tcorr.out") for folder in os.listdir(args.path)}
        highest_cluster = max(folders, key = folders.get)

        sqs_list, cand_list = determine_candidates(path             =args.path, 
                                                   highest_cluster  =highest_cluster,
                                                   sqs_file         =args.candidate_file
                                                   )
        
        perform_match_analysis(out_path=args.output_dir, 
                               sqs_list=sqs_list, 
                               cand_list=cand_list, 
                               num_best=args.num_best, 
                               max_score=len(folders.keys())
                               )

    else:
        copy_best_sqs(path=f"{args.path}",
                      sqs_out=args.out_file,
                      out_path=args.output_dir)
        
    zip_up_output(to_zip=[f"{args.output_dir}/finished"],
                  zip_path=f"{args.output_dir}/lat_ins.zip")

def copy_best_sqs(path, sqs_out, out_path):
    for conc in sorted(os.listdir(path)):
        if not os.path.exists(f'{out_path}/finished/{conc}'):
            os.makedirs(f'{out_path}/finished/{conc}')

        shutil.copyfile(f"{path}/{conc}/{sqs_out}", f"{out_path}/finished/{conc}/{sqs_out}")

def zip_up_output(to_zip, zip_path):
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in to_zip:
            zipf.write(f)


def determine_candidates(path, highest_cluster, sqs_file):
    sqs_lists = {}
    cand_list = {}

    for folder in os.listdir(path):
        if sqs_lists == {}:
            sqs_lists = {conc:[] for conc in sorted(os.listdir(f"{path}/{folder}"))}
            cand_list = {conc:[] for conc in sorted(os.listdir(f"{path}/{folder}"))}

        for conc in sorted(os.listdir(f"{path}/{folder}")):
            sqs_lists[conc] += sqs_list_to_pmg(read_in_lat_list(f"{path}/{folder}/{conc}/unique_{sqs_file}"))
            if folder == highest_cluster:
                cand_list[conc] += sqs_list_to_pmg(read_in_lat_list(f"{path}/{folder}/{conc}/unique_{sqs_file}"))

    return sqs_lists, cand_list


def perform_match_analysis(out_path, sqs_list, cand_list, num_best, max_score):
    matcher = StructureMatcher()

    def score_sqs_amt(str_list, new_str):
        score = 0
        r = []
        for idx in range(len(str_list)):
            str = str_list[idx]
            if matcher.fit(str,new_str):
                r.append(idx)
                score += 1

        for idx in sorted(r, reverse=True):
            str_list.pop(idx)
        
        return str_list, score
    
    multiple_dict = {conc: [] for conc in sqs_list.keys()}
    for conc, l in sqs_list.items():
        if not os.path.exists(f'{out_path}/finished/{conc}'):
            os.makedirs(f'{out_path}/finished/{conc}')

        if conc == 'sqs_00' or conc == 'sqs_01':
            write_lat_list(f'{out_path}/finished/{conc}/best_sqs.out', [l[0]]) 
            continue

        compare_list = l.copy()
        scores = {score: [] for score in range(max_score+1)}

        for pmg_str in cand_list[conc]:
            compare_list, score = score_sqs_amt(compare_list, pmg_str)
            scores[score].append(pmg_str)

        best_sqs = select_best(scores, num_best)
        write_lat_list(f'{out_path}/finished/{conc}/best_sqs.out', best_sqs)


def select_best(scores, target):
    max_score = max(scores)
    ret = []
    
    for curr_score in range(max_score,0,-1): #walk through scores and take high scores until it's not possible
        amt = len(scores[curr_score])

        if amt == (target - len(ret)):
            ret += scores[curr_score]
            break

        elif amt > target:
            while len(ret) != target:
                ret.append(rng.choice(scores[curr_score]))
            break

        elif amt < (target - len(ret)):
            ret += scores[curr_score]
            
        if len(ret) == target:
            break
    
    return ret



if __name__ == '__main__':
    main()