import cv2
import colorsys


class LaserDetector(object):

    LASER_RED = 'RED'
    LASER_GREEN = 'GREEN'
    LASER_REDGREEN = 'RED|GREEN'

    RED_LASER_MIN_HSV = colorsys.rgb_to_hsv(255, 207, 187)
    RED_LASER_MAX_HSV = colorsys.rgb_to_hsv(255, 72, 187)

    def __init__(self, frame):
        self.frame = frame
        self.debug = False


    def detect(self, laser_color=LASER_RED, radius_min=1.5, radius_max=3):
        """Laser shot detection function

        Args:
            laser_color (str): RED, GREEN, RED|GREEN

        Returns:
            tuple | False: False if nothing detected, if detected tuple of (x,y, radius) location

        """

        if laser_color == self.LASER_RED:
            laser_min = self.RED_LASER_MIN_HSV
            laser_max = self.RED_LASER_MAX_HSV
        else:
            laser_min = self.RED_LASER_MIN_HSV
            laser_max = self.RED_LASER_MAX_HSV

        hsv_img = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)

        frame_threshed = cv2.inRange(hsv_img, laser_min, laser_max)

        contours = cv2.findContours(
            frame_threshed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

        center = None

        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)

            if M["m00"] > 0:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            else:
                center = int(x), int(y)

            _x, _y = center

            if self.debug:
                print("Shot Radius: " + str(radius) + " at (" + str(_x) + "," + str(_y) + ")\n")

            # IF the radius renders as a legit detection of the laser
            if radius >= radius_min and radius <= radius_max:
                ret = (_x, _y, radius)
            else:
                ret = False

            return ret
