class ProcessField:
    def __init__(self, camera_field_size, controller):
        self.controller_maxima = controller.get_maxima()
        self.camera_field_size = camera_field_size


    def get_real_pos(self, x, y):
        return {x, y}  # not implemented yet
