
class TargetManager(object):

    NO_TARGETS = -1
    MISS = -2

    def __init__(self):
        self.debug = False
        self.targets = {}

    def define_target(self, cam_index, x1, y1, x2, y2):
        new_target = [x1, y1, x2, y2]
        if cam_index in self.targets.keys():
            self.targets[cam_index].append(new_target)
        else:
            self.targets[cam_index] = [new_target]

    def delete_target(self, cam_index, target_index):
        if cam_index in self.targets.keys():
            del self.targets[cam_index][target_index]

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
            if (sx >= x1) and (sx <= x2) and (sy >= y1) and (sy <= y2):
                hit = self.targets[cam_index].index(target)
                break

        return hit


class ShotManager(object):

    def __init__(self, shot_table=None):
        """
            Args:
                shot_table (gui.ShotTable)
        """
        self.debug = True
        self.shot_table = shot_table
        self.hits = {}
        self.misses = {}

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

    def log_miss(self, cam_index, shot):
        if cam_index in self.misses.keys():
            self.misses[cam_index].append(shot)
        else:
            self.misses[cam_index] = [shot]

        if self.debug:
            x,y,r = shot
            print "Logged MISS for cam("+str(cam_index)+") at ("+str(x)+","+str(y)+")"
    
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