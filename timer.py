import cv2
import time

class Timer(object):

    def __init__(self, start_callable, par_callable):
        self.debug = False
        self.start_callable_called = False
        self.start_callable = start_callable
        self.par_callable_called = False
        self.par_callable = par_callable
        self.startTime = 0.0
        self.elapsedTime = 0.0
        self.delayTime = False
        self.parTime = False 
        self.parTimeMet = False
        self.mainTimerPattern = '%02i:%02i:%02i'
        self.shotLogPattern = '%02i.%02i'
        self.timerRunning = False

    def time_init(self):
        if self.debug:
            print "timer.time_init"

        delay = abs(float(self.delayTime))
        if delay > 0:
            self.elapsedTime = delay * -1
        else:
            self.elapsedTime = 0

        par = abs(float(self.parTime))
        if par > 0:
            self.parTime = par
        else:
            self.parTime = False

    def current_time(self):
        return time.time()

    def time_format_shot_log(self, elap):
        seconds = int(elap)
        hseconds = int((elap - seconds)*100)
        timeStr = self.shotLogPattern % (abs(seconds), abs(hseconds))
        return timeStr

    def time_format_elap(self, elap):
        minutes = int(elap/60)
        seconds = int(elap - minutes*60.0)
        hseconds = int((elap - minutes*60.0 - seconds)*100)
        timeStr = self.mainTimerPattern % (abs(minutes), abs(seconds), abs(hseconds))
        return timeStr

    def time_update(self):
        self.elapsedTime = self.get_current_time()

        if self.delayTime:
            if self.elapsedTime >= 0:
                self.time_delay_time_expired()

        if self.parTime:
            if self.elapsedTime >= self.parTime:
                self.time_par_time_met()
        return self.time_format_elap(self.elapsedTime)

    def start(self):
        if self.debug:
            print "timer.start"

        if not self.timerRunning:
            self.time_init()
            self.startTime = self.current_time() - self.elapsedTime
            self.timerRunning = True
            self.time_update()

    def stop(self):
        if self.debug:
            print "timer.stop"

        if self.timerRunning:
            self.timerRunning = False
            if self.parTimeMet:
                self.elapsedTime = self.parTime
            else:    
                self.elapsedTime = self.current_time() - self.startTime

    def reset(self):
        if self.debug:
            print "timer.reset"

        self.par_callable_called = False
        self.start_callable_called = False
        self.startTime = self.current_time()
        self.time_init()

    def time_par_time_met(self):
        if not self.timerRunning:
            return

        if self.debug:
            print "timer.time_par_time_met"

        if (self.timerRunning):
            self.parTimeMet = True;
            self.stop()

        if self.par_callable_called:
            return 

        self.par_callable_called = True
        self.par_callable()    


    def time_delay_time_expired(self):
        if not self.timerRunning:
            return

        if self.debug:
            print "timer.time_delay_time_expired: " + str(self.start_callable_called)

        if self.start_callable_called:
            return 

        self.start_callable_called = True
        self.start_callable()

    def get_current_time_formatted_elap(self):
        timeStr = self.time_format_elap(self.elapsedTime)
        return timeStr

    def get_current_time(self):
        if (self.timerRunning):
            t = self.current_time() - self.startTime
        else:
            t = self.elapsedTime

        return t