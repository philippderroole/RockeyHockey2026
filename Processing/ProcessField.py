class ProcessField:
    def __init__(self, max_x, max_y):
        self.max_x = max_x  # max values from StepperControllerClass
        self.max_y = max_y

    def get_real_pos_from_img_pos(self, x, y):
        return {x, y}  # not implemented yet
