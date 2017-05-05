import cv2

class TargetManager(object):

    NO_TARGETS = -1
    MISS = -2

    def __init__(self, cam_resize_multiple):
        self.debug = False
        self.cam_resize_multiple = cam_resize_multiple
        self.targets = {}
        self.is_drawing = False
        self.drawing_start_x = None
        self.drawing_start_y = None

    def on_mouse_event(self, event):
        if self.debug:
            print(event.type)

        if event.type == '4': #'<Button-1>':
            self.is_drawing = True
            self.drawing = None
            self.drawing_start_x = event.x
            self.drawing_start_y = event.y
            if self.debug:
                print('Down', event.x, event.y)

        elif event.type == '5': #'<ButtonRelease-1>':
            self.is_drawing = False
            self.drawing = None
            self.define_target(event.widget._cam_index, self.drawing_start_x, self.drawing_start_y, event.x, event.y)
            if self.debug:
                print('Up', event.x, event.y)

        elif event.type == '6': #'<Motion>':
            if self.is_drawing:
                self.drawing = [self.drawing_start_x, self.drawing_start_y, event.x, event.y]
                if self.debug:
                    print('Move', self.drawing_start_x, self.drawing_start_y, event.x, event.y)

    def define_target(self, cam_index, x1, y1, x2, y2):
        new_target = [x1, y1, x2, y2]
        if cam_index in self.targets.keys():
            self.targets[cam_index].append(new_target)
        else:
            self.targets[cam_index] = [new_target]

    def delete_target(self, cam_index, target_index):
        if cam_index in self.targets.keys():
            del self.targets[cam_index][target_index]

    def delete_last_target(self, cam_index):
        if cam_index in self.targets.keys():
            self.targets[cam_index].pop(-1)

    def delete_all_targets(self):
        self.targets = {}        

    def get_targets_for_camera(self, cam_index):
        """Get an array of targets for the given camera

        Args:
            cam_index (int|str): id of the camera

        Returns:
            (array) of target arrays w/ target index [x1,y1,x2,y2]

        """
        if cam_index in self.targets.keys():
            return self.targets[cam_index]
        else:
            return []    

    def shot_is_on_target(self, cam_index, shot):
        """Function to determine if the given shot was within
        the bounds of any of the existing targets

        Args:
            cam_index: index of camera's targets to search
            shot: tuple of shot - (x, y, radius)

        Returns:
            int: NO_TARGETS(-1) for yes, no targets defined; 
                    MISS(-2) for no target hit (miss); 
                    index of hit target  
        """

        if not self.targets:
            return self.NO_TARGETS

        if cam_index not in self.targets.keys():
            return self.NO_TARGETS

        #default miss
        hit = self.MISS

        sx, sy, sr = shot

        for target in self.targets[cam_index]:
            x1, y1, x2, y2 = target
            x1 = x1 / self.cam_resize_multiple
            y1 = y1 / self.cam_resize_multiple
            x2 = x2 / self.cam_resize_multiple
            y2 = y2 / self.cam_resize_multiple

            if (sx >= x1) and (sx <= x2) and (sy >= y1) and (sy <= y2):
                hit = self.targets[cam_index].index(target)
                break

        return hit


class ShotManager(object):

    HIT = 'hit'
    MISS = 'miss'

    def __init__(self, timer):
        self.debug = False
        self.timer = timer
        self.hits = {}
        self.misses = {}
        self.shotTimes = []

    def reset(self):
        self.hits = {}
        self.misses = {}
        self.shotTimes = []

    def shot_count(self):
        total = 0
        for cam_index in self.hits:
            total += len(self.hits[cam_index])
        for cam_index in self.misses:
            total += len(self.misses[cam_index])
        return total

    def log_hit(self, cam_index, target_index, shot):
        x,y,r = shot
        shot_on_target = (x,y,r,target_index)

        if cam_index in self.hits.keys():
            self.hits[cam_index].append(shot_on_target)
        else:
            self.hits[cam_index] = [shot_on_target]

        if self.debug:
            x,y,r = shot
            print "Logged HIT for cam("+str(cam_index)+"), target("+str(target_index)+") at ("+str(x)+","+str(y)+")"

        return self.log_shot_details(self.HIT, cam_index, target_index)

    def log_miss(self, cam_index, shot):
        if cam_index in self.misses.keys():
            self.misses[cam_index].append(shot)
        else:
            self.misses[cam_index] = [shot]

        if self.debug:
            x,y,r = shot
            print "Logged MISS for cam("+str(cam_index)+") at ("+str(x)+","+str(y)+")"

        return self.log_shot_details(self.MISS, cam_index)

    def log_shot_details(self, hit_miss, cam_index, target_index=False):
        if hit_miss == self.HIT:
            tags = ()
        elif hit_miss == self.MISS:
            tags = ('miss')

        shot_num = self.shot_count()

        shot_time = self.timer.get_current_time()
        self.shotTimes.append(shot_time)
        shot_time_str = self.timer.time_format_shot_log(shot_time)
        
        if len(self.shotTimes) >= 2:
            last_time = self.shotTimes[-2]
            split_time = self.timer.time_format_shot_log((shot_time - last_time))
        else:
            split_time = self.timer.time_format_shot_log(0.0)
        
        if target_index == TargetManager.MISS:
            target_num = 'Miss'
        elif target_index == TargetManager.NO_TARGETS:
            target_num = 'N/A'
        else:
            target_num = "Target "+str(target_index + 1)

        target_num = "Cam "+str(cam_index)+", "+ target_num

        return (shot_num, shot_time_str, split_time, target_num, tags)

    
    def get_hits_for_camera(self, cam_index):
        """Get an array of hits for the given camera

        Args:
            cam_index (int|str): id of the camera

        Returns:
            (array) of shot tuples w/ target index (x,y,r, target_index)

        """
        if cam_index in self.hits.keys():
            return self.hits[cam_index]
        else:
            return []

    def get_misses_for_camera(self, cam_index):
        """Get an array of misses for the given camera

        Args:
            cam_index (int|str): id of the camera

        Returns:
            (array) of shot tuples (x,y,r)

        """
        if cam_index in self.misses.keys():
            return self.misses[cam_index]
        else:
            return []      
