# %%
import cv2, sys, yaml, os
import numpy as np
from argparse import ArgumentParser

%pylab inline
# see comments at the end of the document

def extract_data(img_path: str, yaml_path: str):

    # reading in the image and converting to 0 = occupied, 1 = not occupied
    if img_path[-3:] == 'pgm':
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        th, dst = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY) # @Nilou wofür?

    # for infos on parameters: http://wiki.ros.org/map_server
    with open(yaml_path, 'r') as stream:
        map_info = yaml.safe_load(stream)

    return img, map_info


def determine_map_size(img: list, map_info: dict):
    """Determining the image size by using resolution in meters
    """
    return [map_info['resolution'] * _ for _ in img.shape]

def occupancy_ratio(img: list):
    """Proportion of the occupied area
    """
    # TODO to find the actual occupancy only interior occupied pixels should be taken into account
    free_space = np.count_nonzero(img)
    return 1 - free_space/(img.shape[0] * img.shape[1])


def entropy( img_path: str):
    """measures the degree of disorder in the image
    """
    features = []
    # example
    # T = np.array([[255, 255, 255,255, 255,255], [255, 255, 255,255, 255,255], [255, 255, 255,255, 255,255], [255, 255, 255,255, 255,255]])
    th, dst = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY)
    # cv2.imwrite("opencv-threshold-example.jpg", dst)
    # np.savetxt('test.txt', dst)
    windows = sliding_window(dst, 2, (2, 2))
    windowList = []
    for window in windows:
        windowList.append(window)
        featureVector = extractFeatures(window)

    entropy = 0
    for i in featureVector:
        if i != float(0):
            entropy += (i) * np.log(i)
    entropy = (-1) * entropy

    print('calculated entropy:', entropy)
    print('Size of image:', img.shape)

def sliding_window(image, stepSize, windowSize):
    for y in range(0, image.shape[0], stepSize):
        for x in range(0, image.shape[1], stepSize):
            yield (x, y, image[y:y + windowSize[1], x:x + windowSize[0]])

def extractFeatures(window):

    freq_obstacles = window[2] == 0
    total = freq_obstacles.sum()
    density = total * 1/4
    density_gird.append(density)

    return density_gird

def save_information(data: dict, dest: str):
    """To save the evaluated metrics
    args:
        data: data of the evaluated metrics
        dest: path were the data should be saved
    """
    os.chdir(dest)
    with open('complexity.yml', 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

image_path = "/home/elias/catkin_ws/src/forks/arena-tools/aws_house/map.pgm"
yaml_path = "/home/elias/catkin_ws/src/forks/arena-tools/aws_house/map.yaml"
dest_path = "/home/elias/catkin_ws/src/forks/arena-tools/aws_house"

# extract data
# img_data = extract_data(args.image_path, args.yaml_path)
img, map_info = extract_data(image_path, yaml_path)
data = {}

# calculating metrics
# data["Entropy"] = entropy()
data['MapSize'] = determine_map_size(img, map_info)
data["OccupancyRatio"] = occupancy_ratio(img)

# dump results
save_information(data, dest_path)

# NOTE: for our complexity measure we make some assumptions
# 1. We ignore the occupancy threshold. Every pixel > 0 is considert to be fully populated even though this is not entirely accurate since might also only partially be populated (we therefore slightly overestimate populacy.)
