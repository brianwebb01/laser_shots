#! /usr/bin/env python
import argparse
from cv2 import cv
import cv2
import sys
import numpy as np
import pygame
import os
import time
import colorsys
import Tkinter as tk
from PIL import Image
from PIL import ImageTk
import tkMessageBox


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

        self.debug = True

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

        self.window = tk.Tk()
        self.window.resizable(width=False, height=False)
        self.window.wm_title('Laser Tracker')
        self.window.config(background="#FFFFFF")
        self.window.protocol("WM_DELETE_WINDOW", self.handle_quit)
        self.window.bind("q", self.handle_quit)
        self.window.bind('<Key>', self.on_key_event)

        #Graphics window
        self.imageFrame = tk.Frame(self.window, width=320, height=240)
        self.imageFrame.grid(row=0, column=0, padx=10, pady=2)

        #Capture video frames
        self.lmain = tk.Label(self.imageFrame)
        self.lmain.grid(row=0, column=0)
        self.lmain.bind("<Button-1>", self.on_mouse_event)
        self.lmain.bind("<ButtonRelease-1>", self.on_mouse_event)
        self.lmain.bind("<Button-2>", self.on_mouse_event)
        self.lmain.bind("<Motion>", self.on_mouse_event)


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

        self.window.geometry('{}x{}'.format(int((self.cam_width * 1.5)), self.cam_height + 10))

        return self.capture



    def handle_quit(self, delay=10):
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
         

    def show_frame(self):

        success, frame = self.capture.read()

        if not success:
            # no image captured... end the processing
            sys.stderr.write("Could not read camera frame. Quitting\n")
            sys.exit(1)

        #frame = cv2.flip(frame, 1)

        self.detect(frame)

        self.draw_targets(frame)

        self.draw_shots(frame)

        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(10, self.show_frame)     


    def draw_shots(self, frame):
        # draw valid shots
        for shot in self.shots:
            cv2.circle(frame, shot, self.shot_diameter, self.shot_color, -1)

        # draw misses
        for miss in self.misses:
            cv2.circle(frame, miss, self.shot_diameter, self.miss_color, -1)


    def draw_targets(self, frame):
        # draw any defined targets
        for tgt in self.targets:
            x1, y1, x2, y2 = tgt
            cv2.rectangle(frame,(x1, y1), (x2, y2),
                self.targetOutlineColor,
                self.targetOutlineStroke)

        # draw target currently being drawn if any
        if self.drawTarget:
            x1, y1, x2, y2 = self.drawTarget
            cv2.rectangle(frame,
                (x1,y1),
                (x2,y2),
                self.targetOutlineColor,
                self.targetOutlineStroke)



    def on_key_event(self, event):

        if self.debug:
            print("Key pressed:")
            print("char: ", event.char, "keycode: ", event.keycode)
            print "pressed", repr(event.char)

        if event.char == 't':
            if self.targets:
                self.targets.pop(-1)


    def on_mouse_event(self, event):

        if self.debug:
            print(event.type)

        if event.type == '4': #'<Button-1>':
            self.rectangle = True
            self.startpointx = event.x
            self.startpointy = event.y
            if self.debug:
                print('Down', event.x, event.y)

        elif event.type == '5': #'<ButtonRelease-1>':
            self.rectangle = False
            self.drawTarget = None
            self.targets.append([self.startpointx, self.startpointy, event.x, event.y])
            if self.debug:
                print('Up', event.x, event.y)

        elif event.type == '6': #'<Motion>':
            if self.rectangle:
                self.drawTarget = [self.startpointx, self.startpointy, event.x, event.y]
                if self.debug:
                    print('Move', self.startpointx, self.startpointy, event.x, event.y)


    def run(self):
        sys.stdout.write("Using OpenCV version: {0}\n".format(cv2.__version__))

        #time.sleep(3)

        # Set up the camer captures
        self.setup_camera_capture()

        self.show_frame()

        self.window.mainloop()

        #cv2.setMouseCallback('RGB_VideoFrame',self.on_mouse_event)


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
