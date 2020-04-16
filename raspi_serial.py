from __future__ import division, print_function

import logging
import signal
import time
import numpy as np
from time import sleep
from picamera import PiCamera

try:
    import queue
except ImportError:
    import Queue as queue

from robust_serial import write_order, Order, write_i8
from robust_serial.utils import open_serial_port
from constants import BAUDRATE

emptyException = queue.Empty
fullException = queue.Full


serial_file = None
my_file = open('test_photo.jpg', 'wb')
camera = PiCamera()
camera.start_preview()
sleep(2)
camera.capture(my_file)
# At this point my_file.flush() has been called, but the file has
# not yet been closed
my_file.close()


try:
    # Open serial port (for communication with Arduino)
    serial_file = open_serial_port(baudrate=BAUDRATE)

except Exception as e:
    print('exception')
    raise e

is_connected = False
# Initialize communication with Arduino
while not is_connected:
    write_order(serial_file, Order.HELLO)
    bytes_array = bytearray(serial_file.read(1))
    if not bytes_array:
        time.sleep(2)
        continue
    byte = bytes_array[0]
    if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
        is_connected = True

print('start motors')
write_order(serial_file, Order.MOTOR)
write_i8(serial_file, 100) #valeur moteur droit
write_i8(serial_file, 100) #valeur moteur gauche
time.sleep(2)

write_order(serial_file, Order.STOP)
time.sleep(2)
write_order(serial_file, Order.MOTOR)
write_i8(serial_file, -100) #valeur moteur droit
write_i8(serial_file, -100) #valeur moteur gauche

time.sleep(2)

write_order(serial_file, Order.STOP)
camera.stop_preview()
camera.close()
