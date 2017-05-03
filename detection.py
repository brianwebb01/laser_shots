import cv2
import colorsys


class LaserDetector(object):

    LASER_RED = 'RED'
    LASER_GREEN = 'GREEN'
    LASER_REDGREEN = 'RED|GREEN'

    def __init__(self, frame):
        self.frame = frame

        self.debug = False

        self.red_laser_min = colorsys.rgb_to_hsv(255, 207, 187)
        self.red_laser_max = colorsys.rgb_to_hsv(255, 72, 187)

    def detect(self, laser_color=LASER_RED, radius_min=1.5, radius_max=3):
        """Laser shot detection function

        Args:
            laser_color (str): RED, GREEN, RED|GREEN

        Returns:
            tuple | False: False if nothing detected, if detected tuple of (x,y, radius) location

        """

        if laser_color == self.LASER_RED:
            laser_min = self.red_laser_min
            laser_max = self.red_laser_max
        else:
            laser_min = self.red_laser_min
            laser_max = self.red_laser_max

        hsv_img = cv2.cvtColor(self.frame, cv2.cv.CV_BGR2HSV)

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


class TargetManager(object):

    NO_TARGETS = -1
    MISS = -2

    def __init__(self):
        self.debug = False
        self.targets = {}

    def define_target(self, cam_index, x1, y1, x2, y2):
        new_target = [x1, y2, x2, y2]
        if cam_index in self.targets.keys():
            self.targets[cam_index].append(new_target)
        else:
            self.targets[cam_index] = [new_target]

    def delete_target(self, cam_index, target_index):
        if cam_index in self.targets.keys():
            del self.targets[cam_index][target_index]

    def delete_all_targets(self):
        self.targets = {}            

    def shot_is_on_target(self, cam_index, shot):
        """Function to determine if the given shot was within
        the bounds of any of the existing targets

        Args:
            cam_index: index of camera's targets to search
            shot: tuple of shot - (x, y, radius)

        Returns:
            int: NO_TARGETS(-1) for yes, no targets defined; 
                    MISS(-2) for no target hit (miss); 
                    index of hit target  
        """

        if not self.targets:
            return self.NO_TARGETS

        if cam_index not in self.targets.keys():
            return self.NO_TARGETS

        #default miss
        hit = self.MISS

        sx, sy, sr = shot

        for target in self.targets[cam_index]:
            x1, y1, x2, y2 = target
            if (sx >= x1) and (sx <= x2) and (sy >= y1) and (sy <= y2):
                hit = targets.index(target)
                break

        return hit


class ShotManager(object):

    def __init__(self, shot_table=None):
        """
            Args:
                shot_table (gui.ShotTable)
        """
        self.debug = True
        self.shot_table = shot_table
        self.hits = {}
        self.misses = {}

    def log_hit(self, cam_index, target_index, shot):
        x,y,r = shot
        shot_on_target = (x,y,r,target_index)

        if cam_index in self.hits.keys():
            self.hits[cam_index].append(shot_on_target)
        else:
            self.hits[cam_index] = [shot_on_target]

        if self.debug:
            x,y,r = shot
            print "Logged HIT for cam("+str(cam_index)+"), target("+str(target_index)+") at ("+str(x)+","+str(y)+")"

    def log_miss(self, cam_index, shot):
        if cam_index in self.misses.keys():
            self.misses[cam_index].append(shot)
        else:
            self.misses[cam_index] = [shot]

        if self.debug:
            x,y,r = shot
            print "Logged MISS for cam("+str(cam_index)+") at ("+str(x)+","+str(y)+")"
    
    def get_hits_for_camera(self, cam_index):
        """Get an array of hits for the given camera

        Args:
            cam_index (int|str): id of the camera

        Returns:
            (array) of shot tuples w/ target index (x,y,r, target_index)

        """
        if cam_index in self.hits.keys():
            return self.hits[cam_index]
        else:
            return []

    def get_misses_for_camera(self, cam_index):
        """Get an array of misses for the given camera

        Args:
            cam_index (int|str): id of the camera

        Returns:
            (array) of shot tuples (x,y,r)

        """
        if cam_index in self.misses.keys():
            return self.misses[cam_index]
        else:
            return []        
