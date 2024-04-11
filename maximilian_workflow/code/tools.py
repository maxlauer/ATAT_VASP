import os
import sys
import numpy as np
from cluster import Cluster


def check_wdir(base_path, paths):
    for path in paths:
        if not os.path.exists(f"{base_path}/{path}"):
            raise ValueError(f"{base_path}/{path} does not exist")

def get_coordinate_system(path):
    try:
        structure_file = open(path, 'r')
    except:
        print(f"\nFile {path} not found")
        sys.exit()

    lines = structure_file.readlines()
    coordinate_system = np.array([vectors.split() for vectors in lines[:3]], dtype='float32')
    
    return coordinate_system
    
    
def read_out_cluster_file(path, coordinate_system):
    try:
        clusters_file = open(path, 'r')
    except:
        print(f"\nFile {path} not found.")
        sys.exit()

    lines = clusters_file.readlines()
    clusters = []
    data = []
    for line in lines:
        if line != '\n':
            data.append(line)
        else:
            clusters.append(Cluster(data, coordinate_system))
            data = []

    return clusters


def read_out_corr_file(path):
    try:
        corr_file = open(path, 'r')
    except:
        print(f"\nFile {path} not found.")
        sys.exit()

    lines = corr_file.readlines()

    arr = np.array([line.split() for line in lines], dtype='float32')
    num_cand = len(lines)
    num_clus = len(lines[0].split())
    
    return arr, num_cand, num_clus