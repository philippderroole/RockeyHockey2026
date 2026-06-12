import math


# f(x) = mx+b
class Line:
    def __init__(self, p1, p2=None, m=None):
        self.p1 = p1
        if p2 is not None:
            if (p2[0] - p1[0]) == 0:
                self.m = None
                self.b = None
            else:
                self.m = (p2[1] - p1[1]) / (p2[0] - p1[0])
                self.b = p1[1] - self.m * p1[0]
        else:
            self.m = m
            self.b = p1[1] - self.m * p1[0]

    def get_y(self, x):
        if self.m is None or self.b is None:
            return None
        return self.m * x + self.b

    def get_x(self, y):
        if self.m is None or self.b is None:
            return None
        if self.m == 0:
            return self.p1[0]
        return (y - self.b) / self.m

    def get_m(self):
        return self.m

    def get_b(self):
        return self.b

    def get_angle_rad(self):
        if self.m is None:
            return None
        return math.atan(self.m)

    def get_angle(self):
        angle = self.get_angle_rad()
        if angle is None:
            return None
        return math.degrees(angle)
