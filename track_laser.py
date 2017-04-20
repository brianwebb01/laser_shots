#! /usr/bin/env python
import argparse
from cv2 import cv
import cv2
import sys
import numpy as np
import serial
import pygame
import os
import time
import colorsys


class LaserTracker(object):

    def __init__(self, cam_width=640, cam_height=480, hue_min=5, hue_max=6,
                 sat_min=50, sat_max=100, val_min=250, val_max=256,
                 display_thresholds=False):
        """
        * ``cam_width`` x ``cam_height`` -- This should be the size of the
        image coming from the camera. Default is 640x480.

        HSV color space Threshold values for a RED laser pointer are determined
        by:

        * ``hue_min``, ``hue_max`` -- Min/Max allowed Hue values
        * ``sat_min``, ``sat_max`` -- Min/Max allowed Saturation values
        * ``val_min``, ``val_max`` -- Min/Max allowed pixel values

        If the dot from the laser pointer doesn't fall within these values, it
        will be ignored.

        * ``display_thresholds`` -- if True, additional windows will display
          values for threshold image channels.

        """

        self.debug = False

        self.cam_width = cam_width
        self.cam_height = cam_height
        self.hue_min = hue_min
        self.hue_max = hue_max
        self.sat_min = sat_min
        self.sat_max = sat_max
        self.val_min = val_min
        self.val_max = val_max
        self.display_thresholds = display_thresholds

        self.capture = None  # camera capture device
        self.channels = {
            'hue': None,
            'saturation': None,
            'value': None,
            'laser': None,
        }

        # general colors
        self.color_green = (0,255,0)
        self.color_yellow = (0,255,255)
        self.color_blue = (0,0,255)
        self.color_red = (255,0,0)

        # array to store our shots
        self.shots = []
        self.misses = []
        self.sounds = []
        self.gunshot1 = os.path.dirname(os.path.realpath(__file__)) + "/sounds/gun-gunshot-01.mp3"
        self.shot_color = self.color_green
        self.miss_color = self.color_yellow
        self.shot_diameter = 3

        # vars for drawing stuff, targets etc.
        self.rectangle = False
        self.startpointx = None
        self.startpointy = None
        self.targets = []
        self.drawTarget = None
        self.targetOutlineColor = self.color_green  
        self.targetOutlineStroke = 1

        # stuff for playing sounds
        pygame.mixer.init()
        pygame.mixer.music.load(self.gunshot1)


    def create_and_position_window(self, name, xpos, ypos):
        """Creates a named widow placing it on the screen at (xpos, ypos)."""
        # Create a window
        cv2.namedWindow(name, cv2.CV_WINDOW_AUTOSIZE)
        # Resize it to the size of the camera image
        cv2.resizeWindow(name, self.cam_width, self.cam_height)
        # Move to (xpos,ypos) on the screen
        cv2.moveWindow(name, xpos, ypos)



    def setup_camera_capture(self, device_num=0):
        """Perform camera setup for the device number (default device = 0).
        Returns a reference to the camera Capture object.

        """
        try:
            device = int(device_num)
            sys.stdout.write("Using Camera Device: {0}\n".format(device))
        except (IndexError, ValueError):
            # assume we want the 1st device
            device = 0
            sys.stderr.write("Invalid Device. Using default device 0\n")

        # Try to start capturing frames
        self.capture = cv2.VideoCapture(device)

        if not self.capture.isOpened():
            sys.stderr.write("Faled to Open Capture device. Quitting.\n")
            sys.exit(1)

        # set the wanted image size from the camera
        self.capture.set(cv.CV_CAP_PROP_FRAME_WIDTH, self.cam_width)
        self.capture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, self.cam_height)

        return self.capture



    def handle_quit(self, delay=10):
        """Quit the program if the user presses "Esc" or "q"."""
        key = cv2.waitKey(delay)
        c = chr(key & 255)
        if c in ['q', 'Q', chr(27)]:
            sys.exit(0)


    def shot_is_on_target(self, shot):
        if not self.targets:
            return True

        hit = False

        sx, sy = shot

        for target in self.targets:
            x1, y1, x2, y2 = target
            if (sx >= x1) and (sx <= x2) and (sy >= y1) and (sy <= y2):
                hit = True
                break

        return hit


    def detect(self, frame):
        hsv_img = cv2.cvtColor(frame, cv.CV_BGR2HSV)

        
        LASER_MIN = colorsys.rgb_to_hsv(255,207,187)
        LASER_MAX = colorsys.rgb_to_hsv(255,72,187)

        frame_threshed = cv2.inRange(hsv_img, LASER_MIN, LASER_MAX)

        cnts = cv2.findContours(frame_threshed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        center = None

        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x,y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            if M["m00"] > 0:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            else:
                center = int(x), int(y)

            if self.debug:
                sys.stdout.write("Shot Radius: " + str(radius) + "\n")

            # IF the radius renders as a legit detection of the laser
            if radius > 1.5 and radius < 3:
                if self.debug:
                    cv2.circle(frame, (int(x), int(y)), int(radius),(0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (0, 255, 0), -1)


                if self.shot_is_on_target(center):

                    if center not in self.shots:
                        self.shots.append(center)
                        pygame.mixer.music.play()

                else:

                    if center not in self.misses:
                        self.misses.append(center)
         



    def display(self, frame):
        """Display the combined image and (optionally) all other image channels
        NOTE: default color space in OpenCV is BGR.
        """
        cv2.imshow('RGB_VideoFrame', frame)


    def on_mouse_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.rectangle = True
            self.startpointx = x
            self.startpointy = y
            if self.debug:
                print('Down', x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            self.rectangle = False
            self.drawTarget = None
            self.targets.append([self.startpointx, self.startpointy, x, y])
            if self.debug:
                print('Up', x, y)

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.rectangle:
                self.drawTarget = [self.startpointx, self.startpointy, x, y]
                if self.debug:
                    print('Move', self.startpointx, self.startpointy, x, y)


    def run(self):
        sys.stdout.write("Using OpenCV version: {0}\n".format(cv2.__version__))

        #time.sleep(3)

        # create output windows
        self.create_and_position_window('RGB_VideoFrame', 10 + self.cam_width, 0)

        if self.display_thresholds:
            self.create_and_position_window('Thresholded_HSV_Image', 10, 10)
            self.create_and_position_window('Hue', 20, 20)
            self.create_and_position_window('Saturation', 30, 30)
            self.create_and_position_window('Value', 40, 40)

        # Set up the camer captures
        self.setup_camera_capture()

        cv2.setMouseCallback('RGB_VideoFrame',self.on_mouse_event)

        # constant loop from the webcam feed
        while True:
            # 1. capture the current image
            success, frame = self.capture.read()
            if not success:
                # no image captured... end the processing
                sys.stderr.write("Could not read camera frame. Quitting\n")
                sys.exit(1)


            # detect any laser shots
            self.detect(frame)
            

            # draw valid shots
            for shot in self.shots:
                cv2.circle(frame, shot, self.shot_diameter, self.shot_color, -1)

            # draw misses
            for miss in self.misses:
                cv2.circle(frame, miss, self.shot_diameter, self.miss_color, -1)

            # draw any defined targets
            for tgt in self.targets:
                cv2.rectangle(frame,(tgt[0],tgt[1]),(tgt[2],tgt[3]),
                    self.targetOutlineColor,
                    self.targetOutlineStroke)

            # draw target currently being drawn if any
            if self.drawTarget:
                cv2.rectangle(frame,
                    (self.drawTarget[0],self.drawTarget[1]),
                    (self.drawTarget[2],self.drawTarget[3]),
                    self.targetOutlineColor,
                    self.targetOutlineStroke)


            self.display(frame)


            self.handle_quit()




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Laser Tracker')
    parser.add_argument('-W', '--width',
        default=640,
        type=int,
        help='Camera Width'
    )
    parser.add_argument('-H', '--height',
        default='480',
        type=int,
        help='Camera Height'
    )
    parser.add_argument('-u', '--huemin',
        default=5,
        type=int,
        help='Hue Minimum Threshold'
    )
    parser.add_argument('-U', '--huemax',
        default=6,
        type=int,
        help='Hue Maximum Threshold'
    )
    parser.add_argument('-s', '--satmin',
        default=50,
        type=int,
        help='Saturation Minimum Threshold'
    )
    parser.add_argument('-S', '--satmax',
        default=100,
        type=int,
        help='Saturation Minimum Threshold'
    )
    parser.add_argument('-v', '--valmin',
        default=250,
        type=int,
        help='Value Minimum Threshold'
    )
    parser.add_argument('-V', '--valmax',
        default=256,
        type=int,
        help='Value Minimum Threshold'
    )
    parser.add_argument('-d', '--display',
        action='store_true',
        help='Display Threshold Windows'
    )
    params = parser.parse_args()

    tracker = LaserTracker(
        cam_width=params.width,
        cam_height=params.height,
        hue_min=params.huemin,
        hue_max=params.huemax,
        sat_min=params.satmin,
        sat_max=params.satmax,
        val_min=params.valmin,
        val_max=params.valmax,
        display_thresholds=params.display
    )

    tracker.run()
