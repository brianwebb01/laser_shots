# LaserShots

## BACKGROUND:

The application is a laser shot detection application for dry-fire target practice. It monitors a OpenCV VideoCapture to detect the presence of a Laser based on color detection in the frame. The user can optionally define targets and if the laser is detected on a target a hit is tracked, otherwise a miss is logged.  Once a laser color is detected the app draws a circle on the frame where the shot was detected, plays a sound and logs the shot time, split time from previous shot, target number (if any) and the overall time.  The timer function of the app allows for an optional countdown delay before beginning to log shots, and an optional par time when shot detection will stop.  A sound is played at both the start, and par time if given.

The code that presently exists mostly works.  On previous iterations there was no timer and the app was purely OpenCV.  Once the timer feature was added TkInter was used which began to cause issues with GUI interaction since the video capture, laser shot detection and GUI interaction were all running at the same time in the main thread  (or at least that is what I think the issue was).  So I integrated threads and a queue to have the GUI in the main TkInter thread and the video capture, and image processing in separate threads.  Presently the app isn't really functional because of the lag related to the threading, but the laser shot detection seems to work.

## VISION FOR THE APP:

The vision for the application is to process laser shot detection of green or red lasers on multiple video captures at once with those capture devices being either USB web cams or video streams from IP Cameras.  Additionally the lighting conditions of the video stream should be configurable to allow for the normal light conditions of the video capture to be quite dark, with a bright light (from a flash light) shining on the target at the time of the shot (red or green laser).  All detected shots would be shown with times on the main shot timer.

The color of the targets and background they are presented on shouldn't have specific requirements (like target must be blue, background must be white) though best practices can be provided. 

## DEV NOTES

### Features

* multi-processing of cam / shot detection
* random delay
* multi purpose start / stop target
* ? setting: camera frame rate sensitivity to pickup shots
* ? setting: color range sensitivity by camera
* ? setting: light sensitivity by camera?