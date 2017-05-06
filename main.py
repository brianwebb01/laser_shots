#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import cv2
import Tkinter as tk
import ttk
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
        self.debug = False
        self.sidebar_width = 375
        self.frame_padding = 10
        self.camera_res_horiz = 320
        self.camera_res_vert = 240
        self.cam_resize_multiple = 2
        self.camera_devices = {'FaceTime HD Camera':0, 'USB Camera 1': 1}
        self.camera_devices = {'FaceTime HD Camera':0}

        self.init_cameras(self.camera_devices.values())
        self.target_manager = TargetManager(self.cam_resize_multiple)
        self.sound_manager = SoundManager()
        self.timer = Timer(self.evt_timer_started, self.evt_timer_par)
        self.shot_manager = ShotManager(self.timer)
        self.init_gui_elements()
        self.show_video_feeds()

    def init_cameras(self, devices=[0]):
        self.cameras = []
        for d in devices:
            self.cameras.append(VideoCamera().new(d, self.camera_res_horiz, self.camera_res_vert))

    def init_gui_elements(self):
        # main window
        self.grid()
        self.geometry('{}x{}'.format(
            ((self.camera_res_horiz * self.cam_resize_multiple) + self.sidebar_width),
            (len(self.cameras) * ((self.camera_res_vert *
                                   self.cam_resize_multiple) + self.frame_padding))))
        # timer label
        self.label_timer = tk.Label(
            self, text="00:00.00", font=("Helvetica", 48))
        self.label_timer.place(x=700, y=0)

        # buttons
        tk.Button(self, text="Start", command=self.start).place(
            x=647, y=457)
        tk.Button(self, text="Stop", command=self.timer.stop).place(
            x=712, y=457)
        tk.Button(self, text="Reset", command=self.reset).place(
            x=777, y=457)
        tk.Button(self, text="Delete Target", command=self.delete_target).place(
            x=845, y=457)
        self.cam_sel_var = tk.StringVar(self)
        self.cam_sel_var.set(self.camera_devices.keys()[0])
        tk.OptionMenu(self, self.cam_sel_var, *self.camera_devices.keys()).place(x=775, y=425)

        # shot table
        self.shotData = ttk.Treeview(self, selectmode="extended", height=17,
                                     columns=('Shot #', 'Shot Time', 'Split', 'Target #'))
        self.shotData.heading('#0', text="Shot #")
        self.shotData.heading('#1', text="Shot Time")
        self.shotData.heading('#2', text="Split")
        self.shotData.heading('#3', text="Target #")
        self.shotData.column('#1', minwidth=0, width=75,
                             stretch=0, anchor=tk.CENTER)
        self.shotData.column('#2', minwidth=0, width=75,
                             stretch=0, anchor=tk.CENTER)
        self.shotData.column('#3', minwidth=0, width=150,
                             stretch=0, anchor=tk.CENTER)
        self.shotData.column('#0', minwidth=0, width=50,
                             stretch=0, anchor=tk.CENTER)
        # kill the empty last column
        self.shotData.column('#4', minwidth=0, width=0)
        self.shotData.tag_configure(
            'error', background='red', foreground='white')
        self.shotData.tag_configure(
            'miss', background='black', foreground='white')
        self.shotData.place(x=650, y=60)

        # settings ui stuff
        tk.Label(self, text='Delay').place(x=647, y=398)
        tk.Label(self, text='Par').place(x=647, y=425)
        self.entry_delay = tk.Entry(self, width=5)
        self.entry_delay.insert(0, '0')
        self.entry_par = tk.Entry(self, width=5)
        self.entry_par.insert(0, '0')
        self.entry_delay.place(x=700, y=398)
        self.entry_par.place(x=700, y=425)

        # camera image stuff
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

            if self.timer.timerRunning and self.timer.elapsedTime > 0:
                shot = LaserDetector(frame).detect(
                    LaserDetector.LASER_RED, 1.0, 3.0)

                if shot:
                    on_target = self.target_manager.shot_is_on_target(
                        camera_idx, shot)
                    if on_target > TargetManager.MISS:
                        self.log_shot_details(self.shot_manager.log_hit(camera_idx, on_target, shot))
                        self.sound_manager.play_sound(SoundManager.HIT)
                    elif on_target == TargetManager.MISS:
                        self.log_shot_details(self.shot_manager.log_miss(camera_idx, shot))
                        self.sound_manager.play_sound(SoundManager.MISS)

            ShotVisualizer().draw_shots(frame, self.shot_manager.get_hits_for_camera(
                camera_idx), self.shot_manager.get_misses_for_camera(camera_idx))

            TargetVisualizer(self.cam_resize_multiple).draw_targets(
                frame, self.target_manager.get_targets_for_camera(camera_idx))

            if self.target_manager.is_drawing:
                if self.target_manager.drawing_on_cam == camera_idx:
                    TargetVisualizer(self.cam_resize_multiple).draw_target(
                        frame, self.target_manager.drawing)

            self.show_video_frame(frame, camera_idx)

        self.label_timer.configure(text=self.timer.time_update())

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

    def log_shot_details(self, data):

        shot_num, shot_time_str, split_time, target_num, tags = data

        self.shotData.insert('', 'end',
                             text=shot_num,
                             values=(shot_time_str, split_time, target_num),
                             tags=tags)
    
    def start(self):
        if self.debug:
            print "main.start"
        d = abs(float(self.entry_delay.get()))
        p = abs(float(self.entry_par.get()))
        if d > 0:
            self.timer.delayTime = d
        if p > 0:
            self.timer.parTime = p
        self.timer.start()

    def reset(self):
        if self.debug:
            print "main.reset"
        self.timer.reset()
        self.shot_manager.reset()
        self.shotData.delete(*self.shotData.get_children())

    def delete_target(self):
        cam_name = self.cam_sel_var.get()
        cam_index = self.camera_devices[cam_name]
        self.target_manager.delete_last_target(cam_index)

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
