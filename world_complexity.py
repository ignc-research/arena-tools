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
        if img_path[-3:] == 'pgm' or img_path[-3:] =='jpg':
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
            if i+j == 0:
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



    def obst_detection(self, img, file_name):
        areaList = []
        #img = cv2.imread('aws_house.pgm')
        thresh = cv2.threshold(img, 105, 255, cv2.THRESH_BINARY_INV)[1]

        thresh = 255 - thresh

       # cv2.imshow('treh', thresh)
        #self.crop(img)
        result = self.edge_detection(thresh, areaList, file_name)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # binarize the image
        ret, bw = cv2.threshold(gray, 105, 255,
                                cv2.THRESH_BINARY_INV)
        connectivity = 1
        nb_components, output, stats, centroids =cv2.connectedComponentsWithStats(bw, connectivity, cv2.CV_32S)
        sizes = stats[1:, -1]
        nb_components = nb_components - 1
        min_size = 250  # threshhold value for objects in scene
        img2 = np.zeros((img.shape), np.uint8)
        for i in range(0, nb_components + 1):
            # use if sizes[i] >= min_size: to identify your objects
            color = np.random.randint(255, size=3)
            # draw the bounding rectangele around each object
            cv2.rectangle(img2, (stats[i][0], stats[i][1]), (stats[i][0] + stats[i][2], stats[i][1] + stats[i][3]),
                          (0, 255, 0), 2)
            img2[output == i + 1] = color

       # cv2.+
    # how('edges', result)
       # cv2.imshow('image', img2)
       # cv2.waitKey(0)


    def get_contours(self, img):

      #  img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)  # Apply the thresholding
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        canny = cv2.Canny(blurred, 30, 300)
        (cnts, _) = cv2.findContours(canny.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        return cnts



    def edge_detection(self, img,areaList , file_name):

        coordList = []
       # img = cv2.imread('aws_house.pgm')
       # thresh = cv2.threshold(img, 105, 255, cv2.THRESH_BINARY_INV)[1]
       # thresh = 255 - thresh
        cnts = self.get_contours(img)
        print('number of obstacles',len(cnts))
        mask = np.zeros(img.shape[:2], dtype=img.dtype)

        # draw all contours larger than 20 on the mask
        xcoordinate_center = []
        ycoordinate_center=[]
        header_coordination =['Area', 'Length', 'Xcoordinate_center', 'Ycoordinate_center']
        with open("Obstacle_coordinations_{}.csv".format(file_name), "w") as f1:
            writer = csv.writer(f1, delimiter='\t',lineterminator='\n',)
            writer.writerow(header_coordination)
            for c in cnts:
                if cv2.contourArea(c) > 5:
                    area = int(cv2.contourArea(c))
                    areaList.append(area)
                    length = int(cv2.arcLength(c, True))
                    x, y, w, h = cv2.boundingRect(c)
                    cv2.drawContours(mask, [c], 0, (255), -1)
                    M = cv2.moments(c)
                    xcoord = int(M['m10'] / M['m00'])
                    ycoord = int(M['m01'] / M['m00'])
                    xcoordinate_center.append(xcoord)
                    ycoordinate_center.append(ycoord)
                    coordList =[area, length, xcoord, ycoord]
                    writer.writerow(coordList)
                   
        areaSum = sum(areaList)
        print('areaSum', areaSum)
        # apply the mask to the original image
        result = cv2.bitwise_and(img, img, mask=mask)
        cnts = self.get_contours(result)
        obst = result.copy()
        cv2.drawContours(obst, cnts, -1, (255, 0, 0), 2)
       # cv2.imshow('im',  cv2.cvtColor(obst, cv2.COLOR_BGR2RGB))
        for cnt in cnts:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(obst, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return cv2.cvtColor(obst, cv2.COLOR_BGR2RGB)



    def distance(self, image):
        areaList = []
        result = self.edge_detection(image, areaList)
        cter = self.get_contours(result)
        (cnts, _) = contours.sort_contours(cter)
        colors = ((0, 0, 255), (240, 0, 159), (0, 165, 255), (255, 255, 0),
                  (255, 0, 255))
        refObj = None
        for c in cter:  # loop over the contours individually

            # if the contour is not sufficiently large, ignore it
            # if cv2.contourArea(c) < 1:
            #     continue
            # compute the rotated bounding box of the contour
            box = cv2.minAreaRect(c)
            box = cv2.boxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
            box = np.array(box, dtype="int")
            box = perspective.order_points(box)
            cX = np.average(box[:, 0])
            cY = np.average(box[:, 1])
            if refObj is None:
                (tl, tr, br, bl) = box
                (tlblX, tlblY) = self.midpoint(tl, bl)
                (trbrX, trbrY) = self.midpoint(tr, br)
                D = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
                refObj = (box, (cX, cY), D / 0.9)
                continue
            orig = image.copy()
            cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 1)
            cv2.drawContours(orig, [refObj[0].astype("int")], -1, (0, 255, 0), 1)
            refCoords = np.vstack([refObj[0], refObj[1]])
            objCoords = np.vstack([box, (cX, cY)])

            # loop over the original points
            for ((xA, yA), (xB, yB), color) in zip(refCoords, objCoords, colors):
                cv2.circle(orig, (int(xA), int(yA)), 3, color, -1)
                cv2.circle(orig, (int(xB), int(yB)), 3, color, -1)
                cv2.line(orig, (int(xA), int(yA)), (int(xB), int(yB)),
                         color, 1)
                D = dist.euclidean((xA, yA), (xB, yB)) / refObj[2]
                (mX, mY) = self.midpoint((xA, yA), (xB, yB))
                cv2.putText(orig, "{:.1f}in".format(D), (int(mX), int(mY - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                imS = cv2.resize(orig, (500, 960))
                cv2.imshow('image', imS)
                cv2.waitKey(1000)

    def midpoint(self, ptA, ptB):
        return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)


    def get_plots(self, x, y):

        plt.plot(x, y, 'ro')
        plt.show()



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

    # calculating metrics
    Complexity().obst_detection(img_origin, file_name)
   # Complexity().distance(img_origin)
    data["Entropy"], data["MaxEntropy"] = Complexity().entropy(img)

    data['MapSize'] = Complexity().determine_map_size(img, map_info)
    data["OccupancyRatio"] = Complexity().occupancy_ratio(img)
    data["NumObs"] = Complexity().number_of_static_obs(img)


    # dump results
    Complexity().save_information(data, args.dest_path)

    print(data)

# NOTE: for our complexity measure we make some assumptions
# 1. We ignore the occupancy threshold. Every pixel > 0 is considert to be fully populated even though this is not entirely accurate since might also only partially be populated (we therefore slightly overestimate populacy.)
