import numpy as np

""" From the corrdump documentary: Cluster file format (clusters.out)

    for each cluster:
    [multiplicity]
    [length of the longest pair within the cluster]
    [number of points in cluster]
    [coordinates of 1st point] [number of possible species-2] [cluster function]
    [coordinates of 2nd point] [number of possible species-2] [cluster function]
    etc.
"""

class Cluster:

    def __init__(self, data: list, coordinate_system: np.ndarray):
        """
        Input:
        * data - lines in clusters.out from the ATAT package descirbing the cluster
        * coordinate system - coordinate system in lat.in
        
        Use --> determines multiplicty, max node distance, number of nodes and the 
                positions of the nodes of the cluster as instance variables:
                    self.multiplictiy, self.max_distance, self.num_nodes, self.nodes

        Returns => None
        """
        self.multiplicity = int(data[0])
        self.max_distance = float(data[1])
        self.num_nodes = int(data[2])

        try:
            positions_org = [c.strip('\n').split(' ')[0:3] for c in data[3:]]
            positions_frac = np.array(positions_org, dtype='float64').T
        
            positions_cart = np.dot(np.transpose(coordinate_system), positions_frac)
            self.nodes = np.transpose(positions_cart)
        except:
            pass


    def mean_distance(self):
        """
        Input: None

        Use --> determine the mean distance of in the cluster in Angstrom
                
        Returns => mean node distance of the cluster
        """
        def cool_distance(x): #stupid overcomplicated summing with high dimensional transpose cause why not XD
            x = x[np.newaxis,:,:]
            r = np.power(x - np.transpose(x, axes=[1,0,2]), 2)
            r = np.sqrt(np.sum(r, axis=2))

            r = np.sum(np.tril(r))
            return r

        def lame_distance(x): #lame normal python version, with a double sum >:| no linalg :( - stole this one just to check the cool version XD
            diff_sum = 0
            for i in range(self.num_nodes):
                for j in range(i+1, self.num_nodes):
                    diff_sum += np.sqrt(sum([(x[i][xyz]-x[j][xyz])**2 for xyz in range(3)]))
            return diff_sum

        if self.num_nodes == 1 or self.num_nodes == 0:
            return None
        else:
            cool = cool_distance(self.nodes)
            lame = lame_distance(self.nodes)
            if round(cool, 7) != round(lame, 7):
                print('ERROR IN COOL DISTANCE!!!')

            return cool*2/(self.num_nodes-1)/self.num_nodes

