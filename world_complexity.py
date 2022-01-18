import cv2
import numpy




class Complexity:

    def __init__(self):

        self.density_gird= []

    #todo: calculating the frequency of density in density list and divide it by list size
    def entropy(self):
        features=[]
        #example
       # T = numpy.array([[255, 255, 255,255, 255,255], [255, 255, 255,255, 255,255], [255, 255, 255,255, 255,255], [255, 255, 255,255, 255,255]])
        img = cv2.imread('hospital.pgm')
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        th, dst = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY)
       # cv2.imwrite("opencv-threshold-example.jpg", dst)
       # numpy.savetxt('test.txt', dst)
        windows = self.sliding_window(dst, 2, (2, 2))
        windowList= []
        for window in windows:
            windowList.append(window)
            featureVector = self.extractFeatures(window)




        entropy= 0
        for i in featureVector:
            if i != float(0):
                entropy += (i) * numpy.log(i)
        entropy = (-1) * entropy

        print('calculated entropy:', entropy)
        print('Size of image:', img.shape)



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


if __name__ == '__main__':
    Complexity().entropy()
