import cv2
import colorsys
import numpy as np


class LaserDetector(object):

    RED_HSV_MIN_1 = (0, 0, 200)
    RED_HSV_MAX_1 = (20, 100, 255)
    RED_HSV_MIN_2 = (160, 0, 200)
    RED_HSV_MAX_2 = (179, 100, 255)
    GREEN_HSV_MIN = (40, 0, 200)
    GREEN_HSV_MAX = (80, 100, 255)

    def __init__(self, frame):
        self.debug = False
        self.frame = frame

    def detect(self, radius_min=1.0, radius_max=15):
        """Laser shot detection function

        Returns:
            tuple | False: False if nothing detected, if detected tuple of (x,y, radius) location

        """

        bilateral_filtered_image = cv2.bilateralFilter(self.frame, 5, 175, 175)
        cv2.imshow('Bilateral', bilateral_filtered_image)

        edge_detected_image = cv2.Canny(bilateral_filtered_image, 170, 250)
        cv2.imshow('Edge', edge_detected_image)

        _, contours, hierarchy = cv2.findContours(
            edge_detected_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        center = None
        ret = False
        for contour in contours:
            area = cv2.contourArea(contour)
            equi_diameter = np.sqrt(4 * area / np.pi)
            radius = round(equi_diameter / 2, 2)

            M = cv2.moments(contour)
            if M["m00"] > 0:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            else:
                continue

            if radius_min < radius < radius_max and center[0] in range(0, self.frame.shape[0]) and center[1] in range(0, self.frame.shape[1]):
                # compute the center of the contour
                pixel_value = self.frame[center[0], center[1]]
                hsv_value = colorsys.rgb_to_hsv(
                    pixel_value[0], pixel_value[1], pixel_value[2])

                laser_type = None

                for c in range(0, 3):
                    if not self.RED_HSV_MIN_1[c] < hsv_value[c] < self.RED_HSV_MAX_1[c]:
                        break
                    laser_type = 'red1'
                for c in range(0, 3):
                    if not self.RED_HSV_MIN_2[c] < hsv_value[c] < self.RED_HSV_MAX_2[c]:
                        break
                    laser_type = 'red2'
                for c in range(0, 3):
                    if not self.GREEN_HSV_MIN[c] < hsv_value[c] < self.GREEN_HSV_MAX[c]:
                        break
                    laser_type = 'green'

                if laser_type is None:
                    continue
                if self.debug:
                    print(laser_type + " Shot! Radius: " + str(radius) + ", coords: " + "(" + str(center[0]) + "," +
                                     str(center[1]) + ")" + "\n")
                    cv2.circle(self.frame, center, int(radius), (0, 200, 255), 2)
                    cv2.circle(self.frame, center, 5, (255, 0, 0), -1)

                x, y = center
                ret = (x, y, radius)

        return ret
