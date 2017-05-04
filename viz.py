import cv2
import colorsys
from PIL import ImageTk, Image


class ImageProcessor(object):
    def frame_to_imagetk(self, frame, width, height):
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        resized = img.resize((width, height), Image.ANTIALIAS)
        imgtk = ImageTk.PhotoImage(image=resized)
        return imgtk


class TargetVisualizer(object):
    def __init__(self):
        self.debug = False
        self.target_outline_stroke = 1
        self.target_outline_color = (0, 255, 0)
        self.resolution_divisor = 1

    def draw_targets(self, frame, targets=[]):
        for tgt in targets:
            self.draw_target(frame, tgt)

    def draw_target(self, frame, target):
        if target:
            x1, y1, x2, y2 = target
            cv2.rectangle(frame, (x1 / self.resolution_divisor, y1 / self.resolution_divisor), (x2 / self.resolution_divisor, y2 / self.resolution_divisor),
                          colorsys.rgb_to_hsv(*self.target_outline_color),
                          self.target_outline_stroke)

            if self.debug:
                print "Drawing target at (" + str(x1) + "," + str(y1) + ") (" + str(x2) + "," + str(y2) + ")"


class ShotVisualizer(object):
    def __init__(self):
        self.shot_diameter = 1
        self.hit_color = (255, 0, 0)
        self.miss_color = (0, 0, 0)

    def draw_shots(self, frame, hits=[], misses=[]):
        self.draw_hits(frame, hits)
        self.draw_misses(frame, misses)

    def draw_hits(self, frame, hits=[]):
        color = colorsys.rgb_to_hsv(*self.hit_color)
        for _shot in hits:
            x, y, r, t = _shot
            cv2.circle(frame, (x, y), self.shot_diameter, color, -1)

    def draw_misses(self, frame, misses=[]):
        color = colorsys.rgb_to_hsv(*self.miss_color)
        for _shot in misses:
            x, y, r = _shot
            cv2.circle(frame, (x, y), self.shot_diameter, color, -1)
