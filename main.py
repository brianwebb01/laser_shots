#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import cv2
import Tkinter as tk
from PIL import ImageTk, Image
from camera import VideoCamera
from detection import LaserDetector



class LaserShotsApp(tk.Tk):

    def __init__(self,parent):
        tk.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()



    def initialize(self):
		self.sidebar_width = 375
		self.frame_padding = 10
		self.camera_height = 640
		self.camera_width = 480

		self.init_cameras([0,1])
		self.init_gui_elements()
		self.show_video_feeds()



    def init_cameras(self, devices=[0]):
    	self.cameras = []
    	for d in devices:
    		self.cameras.append(VideoCamera(d))



    def init_gui_elements(self):

		#main window
		self.grid()
		self.geometry('{}x{}'.format(
			(self.camera_height + self.sidebar_width),
			(len(self.cameras) * (self.camera_height + self.frame_padding))
			))

		self.imageFrames = []
		self.imageLbls = []

    	#frames for showing cameras
		for camera in self.cameras:

			imageFrame = tk.Frame(self)
			self.imageFrames.append(imageFrame)

			imageLbl = tk.Label(self.imageFrames[-1])
			self.imageLbls.append(imageLbl)

			self.imageLbls[-1]._device = camera.get_device()

			idx = self.cameras.index(camera)

			self.imageFrames[-1].grid(row=(idx*10), column=0)
			self.imageLbls[-1].grid(row=(idx*10), column=0)

			


    def show_video_feeds(self):
		for camera in self.cameras:

			frame = camera.get_frame()

			shot = LaserDetector(frame).detect('RED')
			if shot:
				x, y, r = shot
				cv2.circle(frame, (int(x), int(y)), 20, (0,0,255), 2)

			cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
			img = Image.fromarray(cv2image)
			imgtk = ImageTk.PhotoImage(image=img)

			idx = self.cameras.index(camera)

			self.imageLbls[idx].configure(image=imgtk)
			self.imageLbls[idx]._image_cache = imgtk #avoid garbage collection

		self.after(50, func=lambda: self.show_video_feeds())



if __name__ == "__main__":
    app = LaserShotsApp(None)
    app.title('Laser Shots')
    app.mainloop()