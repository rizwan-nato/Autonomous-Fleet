from __future__ import division
import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera

import platform
import cv2

ON_RASPBERRY = platform.uname()[1] == 'raspberrypi'

from picamera.array import PiRGBArray
from picamera import PiCamera

# sensor modes as detailed in https://picamera.readthedocs.io/en/release-1.13/fov.html#sensor-modes
sensor_modes = [(1920, 1080, 30), (3280, 2464, 15), (3280, 2464, 15), (1640, 1232, 40), (1640, 922, 40),
                (1280, 720, 90), (640, 480, 90)]

RES_HD = 0
RES_FULL_HD = 1
RES_1232 = 3
RES_922 = 4
RES_720 = 5
RES_480 = 6


class Capture:
    """
    Class managing the camera, whether it is run on raspberry or laptop.
    Use read method to get the retval and frame.
    """

    def __init__(self, source=0, sensor_mode=RES_480, frame_rate=0):
        """Initializes the camera and grab a reference to the raw camera capture and return a camera object"""

        if ON_RASPBERRY:
            width, height, max_fps = sensor_modes[sensor_mode]
            if not frame_rate:
                frame_rate = int(2 * max_fps / 3)

            self.cam = PiCamera(sensor_mode=5, resolution=(width, height), framerate=frame_rate)
        else:
            self.cap = cv2.VideoCapture(source)

    def read(self):
        """Return a frame took by the camera in a numpy array format"""

        if ON_RASPBERRY:
            raw_capture = PiRGBArray(self.cam, size=self.cam.resolution)
            self.cam.capture(raw_capture, format="bgr")
            frame = raw_capture.array
            return True, frame
        else:
            return self.cap.read()

    def get_cap(self):
        """Returns the object used to acquire frames"""

        return self.cap

    def __del__(self):
        if not ON_RASPBERRY:
            self.cap.release()


class Processor:

    def __init__(self):
        self.camera_capture = Capture()
        self.trash()
    
    def read(self, percent=1):
        self.trash()
        received, image = self.camera_capture.read()
        if received:
            h, w = image.shape[:2]
            self.image = image[int(h * (1 - percent)):h,:]
    
    def trash(self):
        self.image = None
        self.black_n_white = None
        self.dilated_mask = None
    
    def show(self):
        if self.dilated_mask is not None:
            cv2.imshow("Camera processor", self.dilated_mask)
            cv2.waitKey(1)

    def gray_scale(self):
        if self.image is not None:
            kernel_blur = 5
            blur = cv2.GaussianBlur(self.image, (kernel_blur, kernel_blur), 0)
            ret, thresh1 = cv2.threshold(blur, 168, 255, cv2.THRESH_BINARY)
            hsv = cv2.cvtColor(thresh1, cv2.COLOR_RGB2HSV)

            # Define range of white color in HSV
            lower_white = np.array([0, 0, 168])
            upper_white = np.array([0, 0, 255])

            # Threshold the HSV image
            mask = cv2.inRange(hsv, lower_white, upper_white)

            self.black_n_white = mask

    def get_sorted_contours(self, mask):
        # Find the different contours
        _, contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        return sorted(contours, key=cv2.contourArea, reverse=True)

    def process_line_follow(self, percent=1):
        if self.image is None:
            self.read(percent)

        if self.black_n_white is None:
            self.gray_scale()
        
        # Remove noise
        kernel_erode = np.ones((6, 6), np.uint8)
        eroded_mask = cv2.erode(self.black_n_white, kernel_erode, iterations=1)

        kernel_dilate = np.ones((4, 4), np.uint8)
        dilated_mask = cv2.dilate(eroded_mask, kernel_dilate, iterations=1)

        self.dilated_mask = dilated_mask
        
        return self.get_sorted_contours(dilated_mask)

    def process_intersection(self, percent=1):
        if self.image is None:
            self.read(percent)

        if self.black_n_white is None:
            self.gray_scale()
        
        #Filter horizontal lines
        kernel_erode = np.ones((15, 100), np.uint8)
        eroded_mask = cv2.erode(self.black_n_white, kernel_erode, iterations=1)

        kernel_dilate = np.ones((6, 6), np.uint8)
        dilated_mask = cv2.dilate(eroded_mask, kernel_dilate, iterations=1)
        
        return self.get_sorted_contours(dilated_mask)

    def get_deviation(self, percent=1):
        """
        :param image: image of a line
        :return: a float between -1 and 1 included which embodies the position of the robot compared to the white line
        """
        contours = self.process_line_follow(percent)

        if self.image is not None:
            h, w = self.image.shape[:2]

            if len(contours) > 0:
                M = cv2.moments(contours[0])

                # Centroid
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                cursor = (w/2 - cx) / (w / 2)
                return cursor
            else:
                return None

    def is_in_intersection(self, percent=1):
        contours = self.process_intersection(percent)

        if self.image is not None:
            if len(contours) > 0:
                return cv2.contourArea(contours[0]) > 10000

        return False
