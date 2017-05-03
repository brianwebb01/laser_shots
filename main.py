#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import cv2
import Tkinter as tk
from camera import VideoCamera
from detection import *
from viz import *
from tracking import *


class LaserShotsApp(tk.Tk):

    def __init__(self, parent):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        self.debug = True
        self.sidebar_width = 375
        self.frame_padding = 10
        self.camera_res_horiz = 320
        self.camera_res_vert = 240
        self.camera_frm_width = 640
        self.camera_frm_height = 480

        #self.init_cameras([0, 1])
        self.init_cameras([0])
        self.init_gui_elements()
        self.target_manager = TargetManager()
        self.target_manager.define_target(0, 10, 10, 100, 100)
        self.shot_manager = ShotManager()
        self.show_video_feeds()

    def init_cameras(self, devices=[0]):
        self.cameras = []
        for d in devices:
            self.cameras.append(VideoCamera(
                d, self.camera_res_horiz, self.camera_res_vert))

    def init_gui_elements(self):

            # main window
        self.grid()
        self.geometry('{}x{}'.format(
            (self.camera_frm_width + self.sidebar_width),
            (len(self.cameras) * (self.camera_frm_height + self.frame_padding))
        )
        )

        self.imageFrames = []
        self.imageLbls = []

        # frames for showing cameras
        for camera in self.cameras:

            imageFrame = tk.Frame(self)
            self.imageFrames.append(imageFrame)

            imageLbl = tk.Label(self.imageFrames[-1])
            self.imageLbls.append(imageLbl)

            self.imageLbls[-1]._device = camera.get_device()

            idx = self.cameras.index(camera)

            self.imageFrames[-1].grid(row=(idx * 10), column=0)
            self.imageLbls[-1].grid(row=(idx * 10), column=0)

    def show_video_frame(self, frame, cam_index):
        imgtk = ImageProcessor().frame_to_imagetk(
            frame, self.camera_frm_width, self.camera_frm_height)

        self.imageLbls[cam_index].configure(image=imgtk)
        self.imageLbls[cam_index]._image_cache = imgtk

    def show_video_feeds(self):
        for camera in self.cameras:
            camera_idx = self.cameras.index(camera)

            frame = camera.get_frame()

            shot = LaserDetector(frame).detect(
                LaserDetector.LASER_RED, 1.0, 3.0)

            if shot:
                on_target = self.target_manager.shot_is_on_target(
                    camera_idx, shot)
                if on_target > TargetManager.MISS:
                    self.shot_manager.log_hit(camera_idx, on_target, shot)
                elif on_target == TargetManager.MISS:
                    self.shot_manager.log_miss(camera_idx, shot)

            ShotVisualizer().draw_shots(frame, self.shot_manager.get_hits_for_camera(
                camera_idx), self.shot_manager.get_misses_for_camera(camera_idx))

            TargetVisualizer().draw_targets(
                frame, self.target_manager.get_targets_for_camera(camera_idx))

            self.show_video_frame(frame, camera_idx)

        self.after(50, func=lambda: self.show_video_feeds())


if __name__ == "__main__":
    app = LaserShotsApp(None)
    app.title('Laser Shots')
    app.mainloop()
