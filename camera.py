import cv2

class VideoCamera(object):
    def __init__(self, device=0, cam_width=640, cam_height=480):

        self.device = device

        # Using OpenCV to capture from given device. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.capture = cv2.VideoCapture(device)

        if not self.capture.isOpened():
            raise Exception('Faled to Open Capture device')

        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.capture = cv2.VideoCapture('video.mp4')

        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, cam_width)
        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, cam_height)
    

    def __del__(self):
        self.capture.release()

    def get_device(self):
        return self.device
    

    def get_frame(self):
        success, frame = self.capture.read()

        if not success:
            raise Exception('Could not read camera frame')

        return frame