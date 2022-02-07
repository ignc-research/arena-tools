from unittest import skip
import cv2
import sys
import yaml
import os
import rospkg
import numpy as np
from argparse import ArgumentParser
from collections import Counter
from imutils import contours, perspective
import imutils
from scipy.spatial import distance as dist
from pathlib import Path
import csv
from matplotlib import pyplot as plt
import math
from collections import namedtuple


# TODO s
# - identify interior area @Elias
# - identify objects & contours: ev. with https://learnopencv.com/contour-detection-using-opencv-python-c/
# - calcutlate distance between objects: ev. with https://www.pyimagesearch.com/2016/04/04/measuring-distance-between-objects-in-an-image-with-opencv/
#       To calculate:
#           - Number of static obs


# see comments at the end of the document

class Complexity:

    def __init__(self):
        self.density_gird = []

    def extract_data(self, img_path: str, yaml_path: str):

        # reading in the image and converting to 0 = occupied, 1 = not occupied
        if img_path[-3:] == 'pgm' or img_path[-3:] == 'jpg':
            img_origin = cv2.imread(img_path)
            img = cv2.cvtColor(img_origin, cv2.COLOR_BGR2GRAY)
            # convert image pixels to binary pixels 0 or 255
            th, dst = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY)

        # for infos on parameters: http://wiki.ros.org/map_server
        with open(yaml_path, 'r') as stream:
            map_info = yaml.safe_load(stream)

        return img_origin, img, map_info

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
        return 1 - free_space / (img.shape[0] * img.shape[1])

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
        p_zero = count[0.0] / len(featureVector)
        p_one = count[1] / len(featureVector)
        p_two = count[0.25] / len(featureVector)
        p_five = count[0.5] / len(featureVector)
        p_seven = count[0.75] / len(featureVector)
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
        density = total * 1 / 4
        self.density_gird.append(density)

        return self.density_gird

    def determine_all_pixels_of_this_obs(self, img: list, start_pos: list):
        """Determining all pixels that are occupied by this obstacle
        args:
            img: the floor plan
            obs_list: list to append the occupied pixels
            start_pos: Coordinates were an occupied pixel was detected
        """
        obs_coordinates = []

        # we check all sourounding pixels if there are also occupied. If so they are consitered to belong to this obs.
        for y in range(start_pos[1], img.shape[1]):
            # this is checking if the obstacle extends to the right
            for i, x in enumerate(range(start_pos[0], img.shape[0])):
                if img[x, y] != 0:
                    break
                obs_coordinates.append((x, y))
                # to ensure no occupied pixel is counted twiche we set the pixel to not occupied after it as been detected
                img[x, y] = 205
            # this is checking if the obstacle extends to the left
            for j, x in enumerate(range(0, start_pos[0])):
                if img[x, y] != 0:
                    break
                obs_coordinates.append((x, y))
                # to ensure no occupied pixel is counted twiche we set the pixel to not occupied after it as been detected
                img[x, y] = 0
            if i + j == 0:
                break
        return img, obs_coordinates

    def number_of_static_obs(self, img: list):
        """Determining the obstacle in the image incl. their respective pixels
        args:
            img: floorplan to evaluate
        """
        global obs_list
        obs_list = {}
        obs_num = 0

        # going through every pixel and checking if its occupied
        for pixel_y in range(img.shape[1]):
            for pixel_x in range(img.shape[0]):
                if img[pixel_x, pixel_y] == 0:
                    img, obs_list[obs_num] = self.determine_all_pixels_of_this_obs(
                        img, [pixel_x, pixel_y])
                    obs_num += 1

        return len(obs_list)

    def distance_between_obs(self):
        """Finds distance to all other obstacles
        """
        for key, coordinates in obs_list.items():
            obs_list[f'{key}_dist']

            distances = []
            for key_other, coordinates_other in obs_list.items():
                if key_other == key:
                    skip

                # idea: check for closest coordinate + distance & append this to obslist dist
                # ev. here: https://codereview.stackexchange.com/questions/28207/finding-the-closest-point-to-a-list-of-points
                raise NotImplementedError

    def save_information(self, data: dict, dest: str):
        """To save the evaluated metrics
        args:
            data: data of the evaluated metrics
            dest: path were the data should be saved
        """
        os.chdir(dest)
        with open('complexity.yaml', 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)



    def no_obstacles(self):
        areaList = []
        xcoordinate_center = []
        ycoordinate_center = []
        image = cv2.imread('/home/oem/catkin_ws/src/forks/arena-tools/aws_house/small_warehouse.pgm')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        (thresh, blackAndWhiteImage) = cv2.threshold(gray, 127, 255,
                                                     cv2.THRESH_BINARY)
        #  cv2.imshow('map1',gray)
        blur = cv2.GaussianBlur(gray, (11, 11), 0)
        # cv2.imshow('map2',blur)
        canny = cv2.Canny(blur, 30, 40, 3)
        # cv2.imshow('map3', canny)
        dilated = cv2.dilate(canny, (5, 5), iterations=0)
        #  cv2.imshow('map4',dilated)

        (cnt, hierarchy) = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cv2.drawContours(rgb, cnt, -1, (0, 255, 0), 2)
        #
        cv2.imshow('map5',rgb)
        print("No of circles: ", len(cnt))
        for c in cnt:
            if cv2.contourArea(c) > 1:
                area = int(cv2.contourArea(c))
                areaList.append(area)
                length = int(cv2.arcLength(c, True))
                #  x, y, w, h = cv2.boundingRect(c)
                #  cv2.drawContours(mask, [cnts[4]], 0, (255), -1)
                M = cv2.moments(c)
                xcoord = int(M['m10'] / M['m00'])
                ycoord = int(M['m01'] / M['m00'])
                xcoordinate_center.append(xcoord)
                ycoordinate_center.append(ycoord)
                coordList = [area, length, xcoord, ycoord]
            #    print('area:' ,area)
            #    print('length', length)#
            # print('coordList', coordList)
            # #  writer.writerow(coordList)
        self.world_angles(xcoordinate_center, ycoordinate_center)

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.xaxis.set_ticks_position('top')
        ax.yaxis.grid(linestyle='-', color='gray')
        ax.invert_yaxis()
        ax.plot(xcoordinate_center, ycoordinate_center, 'ro', linewidth=1.5)
        # V this adds the lines V
        for x, y in zip(xcoordinate_center, ycoordinate_center):
            plt.plot([0, x], [0, y], color="blue")
            # ^ this adds the lines ^
            plt.plot(x, y, 0, 0, linestyle='--')
        # plt.text(x + 0.01, y + 0.01, user, fontsize=19)

        plt.show()
        # plt.plot(xcoordinate_center, ycoordinate_center, 'ro')
        # plt.show()
        cv2.waitKey(10000)

        return xcoordinate_center, ycoordinate_center


    def world_angles(self, xCoord, yCoord):

        xIndices = []
        xIndices_interval = []
        intervalPointList = []
        angle = []
        subAngleList = []
        xInterval = [min(xCoord) - 10,
                     min(xCoord) + 10]  # finds the smallest x_coordination and forms an interval with +-10
        print('xInterval', xInterval)
        for (index, item) in enumerate(xCoord):  # find the index of this point to find the corresponding y_coordinate
            if item == min(xCoord):
                xIndices.append(index)

        xMax = max(xCoord)
        yMin = min(yCoord)
        yMax = max(yCoord)
        print(yMax)
        print(xCoord)
        print(yCoord)
        if yCoord[xIndices[
            0]] - 10 > yMin:  # because we want the point with smallest x and y, we should check if y is also the smallest
            yInterval = [yMin - 1, yCoord[xIndices[0]] + 10]
        else:
            yInterval = [yCoord[xIndices[0]] - 10, yCoord[xIndices[0]] + 10]

        orgYInterval = yInterval
        listLength = len(xCoord)
        counter = 0
        while yInterval[1] <= yMax + 10 and xInterval[1] <= xMax + 10: # loop interval in y direction
            for (index, item) in enumerate((xCoord)):  # we find all points that are in this interval
                counter = counter + 1
                if item <= xInterval[1] and item >= xInterval[0]:  #find x and indices of x in interval
                    xIndices_interval.append(index)
                    if yCoord[index] <= yInterval[1] and yCoord[index] >= yInterval[0]:  #find y with indices of x
                        intervalPointList.append([item, yCoord[index]])  #find coordination of point in interval
                        point = [item, yCoord[index]]
                        xCenter = (xInterval[1]- xInterval[0] )/2
                        yCenter = (yInterval[1]- yInterval[0]) /2
                        angle.append(self.get_angle([xInterval[0]+ xCenter, yInterval[0] + yCenter], point)) #calculate angle of all points in interval to the first x,y of interval
                      #  angle.append(self.get_angle([xInterval[0] + xCenter, yInterval[0] + yCenter], point))
                        print('point', point)
                        print('x interval', xInterval)
                        print('y Interval', yInterval)
                        print('center of Interval, ', [xInterval[0] + xCenter, yInterval[0] + yCenter])
                        print('angles to x-axis', angle)
                if listLength == counter:   #when the y interval is over, window should go in x direction and then again in y direction, to find the new points
                    yInterval = [yInterval[1], yInterval[1]+10]
                    sortedAngle = sorted(angle)
                    for index in range(len(sortedAngle)):
                        if index != 0:
                             sub = sortedAngle[index] - sortedAngle[index-1]
                             subAngleList.append(sub)
                    sumAngles = sum(subAngleList)
                    lastAngle = 360 - sumAngles
                    subAngleList.append(lastAngle)
                    print('angles between every obstacle',subAngleList)
                    subAngleList = []
                    angle = []
                    counter = 0
            if not (yInterval[1] <= yMax +10 ):
                xInterval = [xInterval[1], xInterval[1] + 10]
                yInterval = orgYInterval



    Point = namedtuple("Point", ["x", "y"])

    def get_angle(self, p1: Point, p2: Point) -> float:
        """Get the angle of this line with the horizontal axis."""

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        theta = math.atan2(dy, dx)
        angle = math.degrees(theta)  # angle is in (-180, 180]
        if angle < 0:
            angle = 360 + angle

        return angle


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
    converted_dict = vars(args)
    file_name = Path(converted_dict['image_path']).stem

    # extract data
    img_origin, img, map_info = Complexity().extract_data(args.image_path, args.yaml_path)
    data = {}

    Complexity().no_obstacles()
    # calculating metrics
    data["Entropy"], data["MaxEntropy"] = Complexity().entropy(img)

    data['MapSize'] = Complexity().determine_map_size(img, map_info)
    data["OccupancyRatio"] = Complexity().occupancy_ratio(img)
    data["NumObs"] = Complexity().number_of_static_obs(img)

    # dump results
    Complexity().save_information(data, args.dest_path)

    print(data)
#todo: die angle liste soll man trennen, weil gerade in einer liste gespeichert werden und ich weiß nicht,
# welche in welche
# NOTE: for our complexity measure we make some assumptions
# 1. We ignore the occupancy threshold. Every pixel > 0 is considert to be fully populated even though this is not entirely accurate since might also only partially be populated (we therefore slightly overestimate populacy.)
