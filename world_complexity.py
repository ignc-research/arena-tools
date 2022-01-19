import cv2, sys, yaml, os, rospkg
import numpy as np
from argparse import ArgumentParser
from collections import Counter

# see comments at the end of the document

class Complexity:

    def __init__(self):
        self.density_gird= []

    
    def extract_data(self, img_path: str, yaml_path: str):

        # reading in the image and converting to 0 = occupied, 1 = not occupied
        if img_path[-3:] == 'pgm':
            img = cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            th, dst = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY) #convert image pixels to binary pixels 0 or 255

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
        free_space = np.count_nonzero(img)
        return 1 - free_space/(img.shape[0] * img.shape[1])


    def entropy(self):
        features=[]
        #example
       # T = np.array([[255, 255, 255,255, 255,255], [255, 255, 255,255, 255,255], [255, 255, 255,255, 255,255], [255, 255, 255,255, 255,255]])
        img = cv2.imread('hospital.pgm')
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        th, dst = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY)
       # cv2.imwrite("opencv-threshold-example.jpg", dst)
       # np.savetxt('test.txt', dst)
        windows = self.sliding_window(dst, 2, (2, 2))
        windowList= []
        for window in windows:
            windowList.append(window)
            featureVector = self.extractFeatures(window)

        count = Counter(featureVector)
        p_zero = count[0.0]/len(featureVector)
        p_one= count[1]/len(featureVector)
        p_two= count[0.25]/len(featureVector)
        p_five= count[0.5]/len(featureVector)
        p_seven= count[0.75]/len(featureVector)
        pList.append(p_zero)
        pList.append(p_one)
        pList.append(p_two)
        pList.append(p_five)
        pList.append(p_seven)

        entropy= 0
        for pDensity in pList:
            if pDensity != 0:
                entropy += (pDensity) * numpy.log(pDensity)

        entropy = (-1) * entropy
        maxEntropy = numpy.log2(5)

        print('calculated entropy:', entropy)
        print('Max. Entropy:', maxEntropy)



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
    data["Entropy"] = Complexity().entropy()

    # dump results
    Complexity().save_information(data, args.dest_path)

# NOTE: for our complexity measure we make some assumptions
# 1. We ignore the occupancy threshold. Every pixel > 0 is considert to be fully populated even though this is not entirely accurate since might also only partially be populated (we therefore slightly overestimate populacy.)
