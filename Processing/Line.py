import math


class Line:
    def __init__(self, p1, p2=None, m=None):
        self.p1 = p1
        if p2 is not None:
            if(p2[0] - p1[0]) == 0:
                self.m = None
                self.b = None
            else:
                self.m = (p2[1] - p1[1]) / (p2[0] - p1[0])
                self.b = p1[1] - self.m * p1[0]
        else:
            self.m = m
            self.b = p1[1] - self.m * p1[0]

    def get_y(self, x):
        return self.m * x + self.b

    def get_x(self, y):
        return (y - self.b) / self.m

    def get_m(self):
        return self.m

    def get_b(self):
        return self.b

    def get_angle_rad(self):
        return math.atan(self.m)

    def get_angle(self):
        return math.degrees(self.get_angle_rad())
