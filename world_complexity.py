import cv2
import sys
import yaml
import os
import rospkg
import numpy as np
from argparse import ArgumentParser
from collections import Counter
from unittest import skip
from scipy import spatial

# TODO s
# - identify interior area @Elias
# - identify objects & contours: ev. with https://learnopencv.com/contour-detection-using-opencv-python-c/
# - calcutlate distance between objects: ev. with https://www.pyimagesearch.com/2016/04/04/measuring-distance-between-objects-in-an-image-with-opencv/
#       To calculate:
#           - Number of static obs


# see comments at the end of the document

ROBOT_RADIUS = 0.3 # [m]
MIN_INTENDED_WALKWAY_WITH = 0.2 # [m]
MIN_OBS_SIZE = 0.2 # [m]: the obs must be at least 20 cm to avoid detecting obstacles that are not actually there due to miscoloured pixel


class Complexity:

    def __init__(self):
        self.density_gird = []

    def extract_data(self, img_path: str, yaml_path: str):

        # reading in the image and converting to 0 = occupied, 1 = not occupied
        if img_path[-3:] == 'pgm':
            img = cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # convert image pixels to binary pixels 0 or 255
            th, dst = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY)
        else:
            return NotImplementedError

        # for infos on parameters: http://wiki.ros.org/map_server
        with open(yaml_path, 'r') as stream:
            map_info = yaml.safe_load(stream)

        return img, map_info

    def determine_map_size(self, img: list, map_info: dict):
        """Determining the image size by using resolution in meters
        """
        return [map_info['resolution'] * _ for _ in img.shape]

    def occupancy_ratio(self, img: list):
        """Proportion of the occupied area
        """
        # TODO to find the actual occupancy only interior occupied pixels should be taken into account
        # idea get the pos on the sides (a,b,c,d) where the value is first 0, use: https://stackoverflow.com/questions/9553638/find-the-index-of-an-item-in-a-list-of-lists
        free_space = np.count_nonzero(img)
        return 1 - free_space/(img.shape[0] * img.shape[1])

    def occupancy_distribution(self, img: list):
        # Idea: https://jamboard.google.com/d/1ImC7CSPc6Z3Dkxh5I1wX_kkTjEd6GFWmMywHR3LD_XE/viewer?f=0
        raise NotImplementedError

    def entropy(self, img_gray):
        features = []
        th, dst = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY)

        windows = self.sliding_window(dst, 2, (2, 2))
        windowList = []
        for window in windows:
            windowList.append(window)
            featureVector = self.extractFeatures(window)

        pList = []
        count = Counter(featureVector)
        p_zero = count[0.0]/len(featureVector)
        p_one = count[1]/len(featureVector)
        p_two = count[0.25]/len(featureVector)
        p_five = count[0.5]/len(featureVector)
        p_seven = count[0.75]/len(featureVector)
        pList.append(p_zero)
        pList.append(p_one)
        pList.append(p_two)
        pList.append(p_five)
        pList.append(p_seven)

        entropy = 0
        for pDensity in pList:
            if pDensity != 0:
                entropy += (pDensity) * np.log(pDensity)

        entropy = (-1) * entropy
        maxEntropy = np.log2(5)

        print('calculated entropy:', entropy)
        print('Max. Entropy:', maxEntropy)
        return float(entropy), float(maxEntropy)

    def sliding_window(self, image, stepSize, windowSize):
        for y in range(0, image.shape[0], stepSize):
            for x in range(0, image.shape[1], stepSize):
                yield (x, y, image[y:y + windowSize[1], x:x + windowSize[0]])

    def extractFeatures(self, window):

        freq_obstacles = window[2] == 0
        total = freq_obstacles.sum()
        density = total * 1/4
        self.density_gird.append(density)

        return self.density_gird



    def check_surrounding(self, img, i, j, obs_coordinates):
        """Determining all pixels that are occupied by this obstacle
        args:
            img: the floor plan
            i,j: start coordinate of the obstacle
            obs_coordinates: list of coordinates occupied by this obstacle

        return:
            img: floor plan without the obstacle on it
            obs_coordinates: tuple of all pixel-indices occupied by the obstacle
        """
        
        # marking the pixel and setting it to not occupied to avoid double assignment
        obs_coordinates.append((i,j))
        img[i,j] = 205

        # for every point we check in a star pattern, whether the surrounding cells are occupied also
        if img[i-1][j] == 0 and i>=1 : 
            self.check_surrounding(img, i-1, j, obs_coordinates)
        if img[i+1][j] == 0 and i+1 <= img.shape[0]: 
            self.check_surrounding(img, i+1, j, obs_coordinates)
        if img[i][j-1] == 0 and j>=1 : 
            self.check_surrounding(img, i, j-1, obs_coordinates)
        if img[i][j+1] == 0 and i+1 <= img.shape[1]: 
            self.check_surrounding(img, i, j+1, obs_coordinates)
        
        return img, obs_coordinates

    def number_of_static_obs(self, img: list):
        """Determining the obstacle in the image incl. their respective pixels
        args:
            img: floorplan to evaluate
        """
        # to allow more recursive function calls
        sys.setrecursionlimit(20000)
        
        global obs_list
        obs_list = {}
        obs_num = 0
        
        # number of pixels an obstacle must have at least (default = 2)
        min_pix_size = MIN_OBS_SIZE / map_info['resolution']


        # going through every pixel and checking if its occupied
        for pixel_y in range(img.shape[1]):
            for pixel_x in range(img.shape[0]):
                if img[pixel_x, pixel_y] == 0:
                    obs_coordinates = []
                    img, temp = self.check_surrounding(img, pixel_x, pixel_y, obs_coordinates)
                    if len(temp) >= min_pix_size:
                        obs_list[obs_num] = temp
                        obs_num += 1

        return len(obs_list)



    def distance_between_obs(self):
        """Finds distance to all other obstacles
        """
        def do_kdtree(combined_x_y_arrays,points):
            mytree = spatial.cKDTree(combined_x_y_arrays)
            dist, _ = mytree.query(points)
            return dist

        # the walkway should be at least this whide to be considert has walkway
        min_walkway_size = MIN_INTENDED_WALKWAY_WITH / map_info['resolution']

        min_obs_dist = 10000 # large number
        for key, coordinates in obs_list.items():

            distances = []
            for key_other, coordinates_other in obs_list.items():
                if key_other == key: continue
                # this checks the distance between the pixels of the obstacles, and only selects the min distance between the pixels
                dist_between_pixel_arrays = do_kdtree(np.array(coordinates_other),np.array(coordinates))
                min_dist_between_pixel_arrays = min(dist_between_pixel_arrays[dist_between_pixel_arrays>min_walkway_size])
                if min_obs_dist > min_dist_between_pixel_arrays: min_obs_dist = min_dist_between_pixel_arrays

        print(min_obs_dist)
        return(min_obs_dist*map_info['resolution'])

    def save_information(self, data: dict, dest: str):
        """To save the evaluated metrics
        args:
            data: data of the evaluated metrics
            dest: path were the data should be saved
        """
        os.chdir(dest)
        with open('complexity.yaml', 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)


if __name__ == '__main__':

    dir = rospkg.RosPack().get_path('arena-tools')
    # reading in user data
    parser = ArgumentParser()
    parser.add_argument("--image_path", action="store", dest="image_path", default=f"{dir}/aws_house/map.pgm",
                        help="path to the floor plan of your world. Usually in .pgm format",
                        required=False)
    parser.add_argument("--yaml_path", action="store", dest="yaml_path", default=f"{dir}/aws_house/map.yaml",
                        help="path to the .yaml description file of your floor plan",
                        required=False)
    parser.add_argument("--dest_path", action="store", dest="dest_path", default=f"{dir}/aws_house",
                        help="location to store the complexity data about your map",
                        required=False)
    args = parser.parse_args()

    # extract data
    img, map_info = Complexity().extract_data(args.image_path, args.yaml_path)
    data = {}

    # calculating metrics
    data['MapSize'] = Complexity().determine_map_size(img, map_info)
    data["OccupancyRatio"] = Complexity().occupancy_ratio(img)
    data["NumObs"] = Complexity().number_of_static_obs(img)
    data["MinObsDis"] = Complexity().distance_between_obs()
    data["Entropy"], data["MaxEntropy"] = Complexity().entropy(img)

    # dump results
    Complexity().save_information(data, args.dest_path)

    print(data)

# NOTE: for our complexity measure we make some assumptions
# 1. We ignore the occupancy threshold. Every pixel > 0 is considert to be fully populated even though this is not entirely accurate since might also only partially be populated (we therefore slightly overestimate populacy.)


