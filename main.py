#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import cv2
import Tkinter as tk
from camera import VideoCamera
from sounds import SoundManager
from detection import *
from viz import *
from tracking import *
from timer import Timer


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
        self.cam_resize_multiple = 2

        #self.init_cameras([0, 1])
        self.init_cameras([0])
        self.target_manager = TargetManager(self.cam_resize_multiple)
        self.shot_manager = ShotManager()
        self.sound_manager = SoundManager()
        self.timer = Timer(self.evt_timer_started, self.evt_timer_par)
        self.timer.parTime = 10.5
        self.timer.delayTime = 3.5
        self.init_gui_elements()
        self.show_video_feeds()

    def init_cameras(self, devices=[0]):
        self.cameras = []
        for d in devices:
            self.cameras.append(VideoCamera(
                d, self.camera_res_horiz, self.camera_res_vert))

    def init_gui_elements(self):
        self.grid()
        self.geometry('{}x{}'.format(
            ((self.camera_res_horiz * self.cam_resize_multiple) + self.sidebar_width),
            (len(self.cameras) * ((self.camera_res_vert *
                                   self.cam_resize_multiple) + self.frame_padding))))

        self.button_start = tk.Button(self, text="Start", command=self.timer.start).place(x=647, y=457)
        self.button_stop = tk.Button(self, text="Stop", command=self.timer.stop).place(x=712, y=457)
        self.button_reset = tk.Button(self, text="Reset", command=self.timer.reset).place(x=777, y=457)

        self.imageFrames = []
        self.imageLbls = []

        # frames for showing cameras
        for camera in self.cameras:

            imageFrame = tk.Frame(self)
            self.imageFrames.append(imageFrame)

            imageLbl = tk.Label(self.imageFrames[-1])
            imageLbl._device = camera.get_device()
            imageLbl._cam_index = self.cameras.index(camera)

            self.bind_cam_frame_interactions(imageLbl)
            self.imageLbls.append(imageLbl)

            idx = self.cameras.index(camera)

            self.imageFrames[-1].grid(row=(idx * 10), column=0)
            self.imageLbls[-1].grid(row=(idx * 10), column=0)

    def show_video_frame(self, frame, cam_index):
        imgtk = ImageProcessor().frame_to_imagetk(
            frame, (self.camera_res_horiz *
                    self.cam_resize_multiple), (self.camera_res_vert * self.cam_resize_multiple))

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
                    self.sound_manager.play_sound(SoundManager.HIT)
                elif on_target == TargetManager.MISS:
                    self.shot_manager.log_miss(camera_idx, shot)
                    self.sound_manager.play_sound(SoundManager.MISS)

            ShotVisualizer().draw_shots(frame, self.shot_manager.get_hits_for_camera(
                camera_idx), self.shot_manager.get_misses_for_camera(camera_idx))

            TargetVisualizer(self.cam_resize_multiple).draw_targets(
                frame, self.target_manager.get_targets_for_camera(camera_idx))

            if self.target_manager.is_drawing:
                TargetVisualizer(self.cam_resize_multiple).draw_target(
                    frame, self.target_manager.drawing)

            self.show_video_frame(frame, camera_idx)

        t = self.timer.time_update()
        print str(t)

        self.after(50, func=lambda: self.show_video_feeds())

    def bind_cam_frame_interactions(self, widget):
        widget.bind(
            "<Button-1>", lambda event: self.target_manager.on_mouse_event(event))
        widget.bind(
            "<ButtonRelease-1>", lambda event: self.target_manager.on_mouse_event(event))
        widget.bind(
            "<Button-2>", lambda event: self.target_manager.on_mouse_event(event))
        widget.bind(
            "<Motion>", lambda event: self.target_manager.on_mouse_event(event))

    def evt_timer_started(self):
        if self.debug:
            print "\n\n[ TIMER STARTED ]\n\n"
        self.sound_manager.play_sound(SoundManager.START)

    def evt_timer_par(self):
        if self.debug:
            print "\n\n[ PAR MET ]\n\n"
        self.sound_manager.play_sound(SoundManager.PAR)    


if __name__ == "__main__":
    app = LaserShotsApp(None)
    app.title('Laser Shots')
    app.mainloop()
