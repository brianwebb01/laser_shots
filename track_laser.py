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
from Tkinter import *
import ttk
from PIL import Image
from PIL import ImageTk
import threading
import Queue
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

        self.debug = False

        # camera settings
        self.cam_width = cam_width
        self.cam_height = cam_height
        self.hue_min = hue_min
        self.hue_max = hue_max
        self.sat_min = sat_min
        self.sat_max = sat_max
        self.val_min = val_min
        self.val_max = val_max
        self.display_thresholds = display_thresholds


        self.camera_frame_queue = Queue.Queue()
        self.put_frame_thread = None
        self.get_frame_thread = None
        self.is_running = False

        # laser color capture settings
        self.capture = None  # camera capture device
        self.channels = {
            'hue': None,
            'saturation': None,
            'value': None,
            'laser': None,
        }

        # general colors defined in HSV
        self.color_green = (0,255,0)
        self.color_yellow = (0,255,255)
        self.color_blue = (0,0,255)
        self.color_red = (0,1,255)
        self.color_black = (0,0,0)

        # array to store our shots
        self.shots = []
        self.misses = []
        self.sounds = []
        self.gunshot1 = os.path.dirname(os.path.realpath(__file__)) + "/sounds/gun-gunshot-01.mp3"
        self.shot_color = self.color_red
        self.miss_color = self.color_black
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


        #UI configs
        self.window = tk.Tk()
        self.window.resizable(width=False, height=False)
        self.window.wm_title('Laser Tracker')
        self.window.config(background="#FFFFFF")
        self.window.protocol("WM_DELETE_WINDOW", self.handle_quit)
        self.window.bind("q", self.handle_quit)
        self.window.bind('<Key>', self.on_key_event)

        #Graphics window
        self.imageFrame = tk.Frame(self.window, width=320, height=240)
        self.imageFrame.grid(row=0, column=0, padx=0, pady=0)

        #Capture video frames
        self.lmain = tk.Label(self.imageFrame)
        self.lmain.grid(row=0, column=0)
        self.lmain.bind("<Button-1>", self.on_mouse_event)
        self.lmain.bind("<ButtonRelease-1>", self.on_mouse_event)
        self.lmain.bind("<Button-2>", self.on_mouse_event)
        self.lmain.bind("<Motion>", self.on_mouse_event)


        # Our time structure [min, sec, centsec]
        self.mainTimer = [0, 0, 0]
        self.mainTimerPattern = '{0:02d}:{1:02d}:{2:02d}'
        self.mainTimerText = tk.Label(self.window, text="00:00:00", font=("Helvetica", 48))
        self.mainTimerText.place(x=700, y=0)
        self.timerRunning = False

        # shot data tree
        self.shotData = ttk.Treeview(self.window, selectmode="extended", height=17,
            columns=('Shot #', 'Shot Time', 'Split', 'Target #', 'Total Time'))
        self.shotData.heading('#0', text="Shot #")
        self.shotData.heading('#1', text="Shot Time")
        self.shotData.heading('#2', text="Split")
        self.shotData.heading('#3', text="Target #")
        self.shotData.heading('#4', text="Total Time")
        self.shotData.column('#1', minwidth=0,width=75, stretch=NO, anchor=tk.CENTER)
        self.shotData.column('#2', minwidth=0,width=75, stretch=NO, anchor=tk.CENTER)
        self.shotData.column('#3', minwidth=0,width=75, stretch=NO, anchor=tk.CENTER)
        self.shotData.column('#4', minwidth=0,width=75, stretch=NO, anchor=tk.CENTER)
        self.shotData.column('#0', minwidth=0,width=50, stretch=NO, anchor=tk.CENTER)
        self.shotData.column('#5', minwidth=0,width=0) #kill the empty last column
        self.shotData.tag_configure('error', background='red', foreground='white')
        self.shotData.tag_configure('miss', background='black', foreground='white')
        self.shotData.place(x=650, y=60)


        for i in [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40]:
            if i == 3:
                tags = ('error')
            elif i == 5:    
                tags = ('miss')
            else:
                tags = ()
            self.shotData.insert('', 'end', text=i, values=("0.10", "0.20", "A", "1.10"), tags=tags)

        # control buttons
        self.button_start = tk.Button(self.window, text="Start", command=self.start)
        self.button_start.place(x=647, y=457)
        self.button_stop = tk.Button(self.window, text="Stop", command=self.stop)
        self.button_stop.place(x=712, y=457)
        self.button_reset = tk.Button(self.window, text="Reset", command=self.reset)
        self.button_reset.place(x=777, y=457)

    def start(self):
        print("start")
        self.timerRunning = True

    def stop(self):
        print("stop")    
        self.timerRunning = False

    def reset(self):
        print("reset")
        self.mainTimer = [0, 0, 0]
        self.mainTimerText.configure(text='00:00:00')

    def update_timeText(self):
        if (self.timerRunning):
            # Every time this function is called, 
            # we will increment 1 centisecond (1/100 of a second)
            self.mainTimer[2] += 1
            
            # Every 100 centisecond is equal to 1 second
            if (self.mainTimer[2] >= 100):
                self.mainTimer[2] = 0
                self.mainTimer[1] += 1
            # Every 60 seconds is equal to 1 min
            if (self.mainTimer[1] >= 60):
                self.mainTimer[0] += 1
                self.mainTimer[1] = 0
            # We create our time string here
            timeString = self.mainTimerPattern.format(self.mainTimer[0], self.mainTimer[1], self.mainTimer[2])
            # Update the timeText Label box with the current time
            self.mainTimerText.configure(text=timeString)
            # Call the update_timeText() function after 1 centisecond
        self.window.after(10, self.update_timeText)    



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

        self.window.geometry('{}x{}'.format(int((self.cam_width + 375)), self.cam_height + 10))

        return self.capture



    def handle_quit(self, delay=10):
        self.is_running = False

        if self.put_frame_thread.isAlive():
            self.put_frame_thread._Thread__stop()
            self.put_frame_thread = None

        if self.get_frame_thread.isAlive():
            self.get_frame_thread._Thread__stop()
            self.get_frame_thread = None

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
         
    def capture_frame(self):
        if self.is_running:
            success, frame = self.capture.read()

            if not success:
                # no image captured... end the processing
                sys.stderr.write("Could not read camera frame. Quitting\n")
                sys.exit(1)

            if self.camera_frame_queue.empty():
                self.camera_frame_queue.put(frame)

            time.sleep(1/250.0)
            self.capture_frame()


    def show_frame(self):

        if self.is_running:
            if not self.camera_frame_queue.empty():
                frame = self.camera_frame_queue.get()
                #frame = cv2.flip(frame, 1)

                self.detect(frame)

                self.draw_targets(frame)

                self.draw_shots(frame)

                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                self.lmain.imgtk = imgtk
                self.lmain.configure(image=imgtk)

            time.sleep(1/500.0)
            self.show_frame()


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

        self.setup_camera_capture()

        #self.show_frame()

        self.is_running = True
        self.put_frame_thread = threading.Thread(target=self.capture_frame)
        self.put_frame_thread.start()
        self.get_frame_thread = threading.Thread(target=self.show_frame)
        self.get_frame_thread.start()


        self.update_timeText()

        self.window.mainloop()


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
