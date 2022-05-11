# Gets Input(Image) from a VideoStream and transforms and warps the Image so that
# the resulting image has always the same dimensions and the robot- and human-line are on the same side
# The game-field in the image has to be put manually by calling chooseCorner()
# -> Left-MouseClick = Robot-Corner AND Right-MouseClick = Human-Corner
# After the corners have been selected you can choose wheter or not you want to keep the corners or try again (so far in the terminal)
# After the corners have been selected you can choose wheter or not you want to flip the image (so far in the terminal)

import cv2
import numpy as np
import matplotlib.pyplot as plt

from Constants import constants

# Test-Images
# img = cv2.imread("Processing/field_TestImages/test_image.jpeg", 1)
# img = cv2.resize(img, (0, 0), fx=0.7, fy=0.7)


class ProcessField:
    def __init__(self, videoStream=0):
        self.videostream = videoStream
        frame, amountOfFrames = self.videostream.readWithFrames()
        # frame = cv2.resize(frame, (0, 0), fx=0.7, fy=0.7)
        self.image = frame.copy()
        self.draw_img = frame.copy()
        self.ptHuman = [[1647, 919], [1644, 183]]

        self.ptRobot = [[165, 180], [177, 919]]

        # Points in the source image: Corners of the game-field. values getting set by self.chooseCorner()
        self.pts1 = np.float32([[56, 65], [368, 52], [28, 387], [389, 390]])

        # Points(And therefore dimensions) for the destination-image.
        self.pts2 = np.float32(
            [
                [0, 0],
                [constants.FIELD_HEIGHT, 0],
                [0, constants.FIELD_WIDTH],
                [constants.FIELD_HEIGHT, constants.FIELD_WIDTH],
            ]
        )
        self.pts2NotSuitable = np.float32(
            [
                [0, 0],
                [constants.FIELD_WIDTH, 0],
                [0, constants.FIELD_HEIGHT],
                [constants.FIELD_WIDTH, constants.FIELD_HEIGHT],
            ]
        )
        self.height = int(self.pts2[3, 0])
        self.length = int(self.pts2[3, 1])
        # the amount of rotation(clock-wise)
        self.rotate = 0
        # True -> larger width than height (Goal-line left and right); False -> larger height than width (Goal-line top and bottom)
        self.suitableForm = True
        # True -> Flip Image vertically: Change left and right for robot
        self.flipImage = False

        self.choosenCorner = False

    def click_event(self, event, x, y, flags, param):
        # checking for left mouse clicks
        if event == cv2.EVENT_LBUTTONDOWN and len(self.ptRobot) < 2:
            print(x, y)
            pt = [x, y]
            self.ptRobot.append(pt)
            print(self.ptRobot)

            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(
                self.draw_img, "Roboter", (x + 10, y + 10), font, 0.9, (0, 0, 255), 2
            )
            # circle outside point
            cv2.circle(self.draw_img, (x, y), 10, (0, 0, 255), 2)
            # point
            cv2.circle(self.draw_img, (x, y), 2, (0, 0, 255), -1)
            cv2.imshow("image", self.draw_img)

        # checking for right mouse clicks
        elif event == cv2.EVENT_RBUTTONDOWN and len(self.ptHuman) < 2:
            pt = [x, y]
            self.ptHuman.append(pt)
            print(self.ptHuman)

            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(
                self.draw_img, "Mensch", (x + 10, y + 10), font, 0.9, (255, 0, 0), 2
            )
            # circle outside point
            cv2.circle(self.draw_img, (x, y), 10, (255, 0, 0), 2)
            # point
            cv2.circle(self.draw_img, (x, y), 2, (255, 0, 0), -1)
            cv2.imshow("image", self.draw_img)

    def chooseCorner(self):
        # print(self.image)
        # Show image as long as there aren't 4 corners for the field
        # Quit by pressing "q"
        #while True:
        #    while True:
        #        key = cv2.waitKey(1)
        #        # Enter or "q"
        #        if key == 13 or key == ord("q"):
        #            break
        #        cv2.imshow("image", self.draw_img)
        #        cv2.setMouseCallback("image", self.click_event)
        #    if len(self.ptRobot) == 2 and len(self.ptHuman) == 2:
        #        break
        # cv2.waitKey(0)
        #cv2.destroyAllWindows()

        # height = self.image.shape[0]
        # width = self.image.shape[1]

        newList = []
        # the amount of rotation(clock-wise)
        self.rotate = 0
        # True -> larger width than height (Goal-line left and right); False -> larger height than width (Goal-line top and bottom)
        self.suitableForm = True
        # Check if the goal-lines are "left and right" or "top and bottom". If true: The difference between the x-values of the human and robot-line is bigger than the y-values. Therefore the lines are "left and right"
        if abs(
            (self.ptRobot[0][0] + self.ptRobot[1][0])
            - (self.ptHuman[0][0] + self.ptHuman[1][0])
        ) > abs(
            (self.ptRobot[0][1] + self.ptRobot[1][1])
            - (self.ptHuman[0][1] + self.ptHuman[1][1])
        ):
            # Check wheter robot is on the right or left side. If true: robot on the right side
            if (self.ptRobot[0][0] + self.ptRobot[1][0]) > (
                self.ptHuman[0][0] + self.ptHuman[1][0]
            ):
                self.rotate = 180
                # Check which point is on top: If true: first point on top
                if self.ptHuman[0][1] < self.ptHuman[1][1]:
                    newList.append(self.ptHuman[0])

                    if self.ptRobot[0][1] < self.ptRobot[1][1]:
                        newList.append(self.ptRobot[0])
                        newList.append(self.ptHuman[1])
                        newList.append(self.ptRobot[1])
                    else:
                        newList.append(self.ptRobot[1])
                        newList.append(self.ptHuman[1])
                        newList.append(self.ptRobot[0])
                else:
                    newList.append(self.ptHuman[1])

                    if self.ptRobot[0][1] < self.ptRobot[1][1]:
                        newList.append(self.ptRobot[0])
                        newList.append(self.ptHuman[0])
                        newList.append(self.ptRobot[1])
                    else:
                        newList.append(self.ptRobot[1])
                        newList.append(self.ptHuman[0])
                        newList.append(self.ptRobot[0])
            # robot on the left side
            else:

                # Check which point is on top: If true: first point on top
                if self.ptRobot[0][1] < self.ptRobot[1][1]:
                    newList.append(self.ptRobot[0])

                    if self.ptHuman[0][1] < self.ptHuman[1][1]:
                        newList.append(self.ptHuman[0])
                        newList.append(self.ptRobot[1])
                        newList.append(self.ptHuman[1])
                    else:
                        newList.append(self.ptHuman[1])
                        newList.append(self.ptRobot[1])
                        newList.append(self.ptHuman[0])
                else:
                    newList.append(self.ptRobot[1])

                    if self.ptHuman[0][1] < self.ptHuman[1][1]:
                        newList.append(self.ptHuman[0])
                        newList.append(self.ptRobot[0])
                        newList.append(self.ptHuman[1])
                    else:
                        newList.append(self.ptHuman[1])
                        newList.append(self.ptRobot[0])
                        newList.append(self.ptHuman[0])
        else:
            self.suitableForm = False
            # Check wheter robot is on the top or bottom. If true: robot on the top
            if (self.ptRobot[0][1] + self.ptRobot[1][1]) < (
                self.ptHuman[0][1] + self.ptHuman[1][1]
            ):
                self.rotate = 270
                if self.ptRobot[0][0] < self.ptRobot[1][0]:
                    newList.append(self.ptRobot[0])
                    newList.append(self.ptRobot[1])
                else:
                    newList.append(self.ptRobot[1])
                    newList.append(self.ptRobot[0])

                if self.ptHuman[0][0] < self.ptHuman[1][0]:
                    newList.append(self.ptHuman[0])
                    newList.append(self.ptHuman[1])
                else:
                    newList.append(self.ptHuman[1])
                    newList.append(self.ptHuman[0])
            # robot on bottom
            else:
                self.rotate = 90
                if self.ptHuman[0][0] < self.ptHuman[1][0]:
                    newList.append(self.ptHuman[0])
                    newList.append(self.ptHuman[1])
                else:
                    newList.append(self.ptHuman[1])
                    newList.append(self.ptHuman[0])

                if self.ptRobot[0][0] < self.ptRobot[1][0]:
                    newList.append(self.ptRobot[0])
                    newList.append(self.ptRobot[1])
                else:
                    newList.append(self.ptRobot[1])
                    newList.append(self.ptRobot[0])

        # Check form of img
        # if (width > height):
        # Check wheter robot is on the right or left side. If true: right side
        # if ((self.ptRobot[0][0] + self.ptRobot[1][0]) > (self.ptHuman[0][0] + self.ptHuman[1][0])):

        self.pts1 = np.asarray(newList, np.float32)
        # print(self.pts1)

        """ test = np.asarray(self.ptRobot, np.float32)
        print(test)
        test2 = np.asarray(self.ptHuman, np.float32)
        print(test2)
        test3 = np.append(test, test2, axis=0)
        print(test3)
        print(self.pts1) """

        if self.suitableForm == False:
            self.pts2 = self.pts2NotSuitable

        self.height = int(self.pts2[3, 0])
        self.length = int(self.pts2[3, 1])

        M = cv2.getPerspectiveTransform(self.pts1, self.pts2)
        dst = cv2.warpPerspective(self.image, M, (self.height, self.length))

        if self.rotate == 180:
            dst = cv2.rotate(dst, cv2.cv2.ROTATE_180)
        elif self.rotate == 90:
            dst = cv2.rotate(dst, cv2.cv2.ROTATE_90_CLOCKWISE)
        elif self.rotate == 270:
            dst = cv2.rotate(dst, cv2.cv2.ROTATE_90_COUNTERCLOCKWISE)

        plt.subplot(121), plt.imshow(self.image), plt.title("Input")
        plt.subplot(122), plt.imshow(dst), plt.title("Output")
        plt.show()

        #answer_corners_ok = None
        #while answer_corners_ok not in ("1", "2"):
        #    answer_corners_ok = input("1 -> Feld passt. 2 -> Ecken erneut setzen: ")
        #    if answer_corners_ok == "1":
        #        continue
        #    elif answer_corners_ok == "2":
        #        self.ptHuman = []
        #        self.ptRobot = []
        #        self.draw_img = img.copy()
        #        self.chooseCorner()
        #        return
        #    else:
        #        print("Bitte gebe 1 oder 2 ein")

        # Answer wether or not you want to flip the camera-input vertically.
        # If you flip: left and right for the robot gets switched
        #answerFlip = None
        #while answerFlip not in ("J", "j", "n", "N"):
        #    answerFlip = input("Willst du das Bild spiegeln? (J/N): ")
        #    if answerFlip == "j" or answerFlip == "J":
        #        self.flipImage = True
        #        flippedDst = cv2.flip(dst, 0)
        #        plt.imshow(flippedDst), plt.title("Output")
        #        plt.show()
        #    elif answerFlip == "n" or answerFlip == "N":
        #        self.flipImage = False
        #    else:
        #        print("Bitte gebe (J/N) ein. J = Ja und N = Nein.")

        self.choosenCorner = True

    def getImage(self):
        # Because the flow of the programm doesn't use getImage() before chooseCorner() got called, this query is useless for now.
        # If you want to add a function where the whole images from the camera are getting used, here it is
        """if self.chooseCorner == False:
            answerCorner = None
            while answerCorner not in ("J", "j", "n", "N"):
                answerCorner = input("Du hast noch keine Ecken für das Spielfeld ausgewählt. Mit dem ganzen Bild fortfahren? (J/N): ")
                if answerCorner == "j" or answerCorner == "J":
                    return self.videoStream.getImage()
                elif answerCorner == "n" or answerCorner == "N":
                    self.chooseCorner()
                else:
                    print("Bitte gebe (J/N) ein. J = Ja und N = Nein.")

        else:"""

        img, amountOfFrames = self.videostream.readWithFrames()
        if amountOfFrames == 0:
            return (img, 0)
        M = cv2.getPerspectiveTransform(self.pts1, self.pts2)
        dst = cv2.warpPerspective(img, M, (self.height, self.length))

        if self.rotate == 180:
            dst = cv2.rotate(dst, cv2.cv2.ROTATE_180)
        elif self.rotate == 90:
            dst = cv2.rotate(dst, cv2.cv2.ROTATE_90_CLOCKWISE)
        elif self.rotate == 270:
            dst = cv2.rotate(dst, cv2.cv2.ROTATE_90_COUNTERCLOCKWISE)

        if self.flipImage == True:
            dst = cv2.flip(dst, 0)

        return (dst, amountOfFrames)


if __name__ == "__main__":
    pass

    test = ProcessField()
    test.chooseCorner()

    print("EXIT")
    exit
