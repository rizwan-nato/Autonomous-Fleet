# coding: utf-8

# import des bibliothèques nécessaires au projet
from __future__ import division, print_function
import zmq
import sys
import time
import camera

# import de la bibliothèque liaison série   
from robust_serial import write_order, Order, write_i8, read_i16, read_i8
from robust_serial.threads import CommandThread, ListenerThread
from robust_serial.utils import open_serial_port
from constants import BAUDRATE

from motor_commands import line_command


# initialisation de la communication avec la raspberry
def init_raspberry():
    serial_file = None
    try:
        # ouvre la liaison série avec l'arduino
        serial_file = open_serial_port(baudrate=BAUDRATE)
        print(serial_file)
    except Exception as e:
        print('exception')
        raise e

    is_connected = False
    # Initialize communication with Arduino
    while not is_connected:
        write_order(serial_file, Order.HELLO)
        bytes_array = bytearray(serial_file.read(1))
        print(bytes_array)
        if not bytes_array:
            time.sleep(2)
            continue
        byte = bytes_array[0]
        if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
            is_connected = True

    return serial_file


# recupere l'identifiant pour la liaison série avec la raspberry
serial_file = init_raspberry()

# init camera
camera_processor = camera.Processor()

# N° d'IP du serveur
ip = "192.168.137.32"
if len(sys.argv) > 1:
    ip = sys.argv[1]

# nom du robot
name = 'bot001'
if len(sys.argv) > 2:
    name = sys.argv[2]

# connection initiale du robot sur le serveur
ctx = zmq.Context()
reqaddr = "tcp://{}:5005".format(ip)
reqsock = ctx.socket(zmq.REQ)
reqsock.connect(reqaddr)

# envoie le message initial pour enregistrer le robot sur le serveur
print("initial hello msg ...")
# envoi d'un message de connection (avec uniquement un 'from')
msg = {"from": name}
reqsock.send_pyobj(msg)
# recupération de la réponse
rep = reqsock.recv_pyobj()
print("received:{}".format(rep))

# création du serveur en mode écoute pour
# répondre aux sollicitations du serveur
subaddr = "tcp://{}:6006".format(ip)
subsock = ctx.socket(zmq.SUB)
subsock.connect(subaddr)
subsock.setsockopt(zmq.SUBSCRIBE, b"")

running = True

# procedure pour répondre aux sollicitations du serveur
def process_msg(msg):
    global running, L_deplacement
    # verifie si le message est destiné au robot
    # s'il y a un champ 'to' et que le nom n'est pas celui du robot
    # on oublie le message
    if "to" in msg and msg["to"] != name:
        print("this msg wasn't for me...")

    # sinon traitement des différents messages reçus
    else:
        if "deplacement" in msg:
            L_deplacement = msg["deplacement"]
        if "command" in msg:
            if msg['command'] == "stop":
                running = False
            elif msg['command'] == "start":
                running = True
def get_list():
    got = False
    L = []
    while not got:
        rep = reqsock.recv_pyobj()
        if rep["to"] == name:

            print("message: ", rep)
            L = rep["deplacement"]
            got = True
    return L

##            if type(msg["commande"]) == list:
# la liste contient la posistion des robots, des obstacles et de la destination :
# L = [{1:(2,4),2:(1,4)}, [(1,1)], (4,4)]

# boucle principale d'écoute et de traitement des évènements
turning = None
# turning_timer_threshold = 30
turning_timer_threshold = 1.2
turning_around_timer_threshold = 2
# turning_timer = 0
turning_start_time = 0
turning_around_start_time = 0

straight = False
# straight_timer = 0
straight_start_time = 0
# straight_timer_threshold = 65
straight_timer_threshold = 5
intersection_counter = 0
intersection_counter_threshold = 3
L_deplacement = []
instructions_done = 0
turn_instruction = ""

obstacle_presence = 0
obstacle_definitive_threshold = 20

# Demande d'envoi de la liste de déplacements
msg = {"deplacement": "send"}
msg["name"] = name
msg["start"] = "ramp"
reqsock.send_pyobj(msg)
L_deplacement = get_list()

#L_deplacement = ["right"]
#L_deplacement = ["straight","straight"]
compteur = 0
while True:
    if compteur % 100 == 0:
        serial_message = serial_file.read()
        compteur = 0
    
        ## SI il y a un obstacle
        if serial_message == b'\x01' and turning is None:
            obstacle_presence = min(obstacle_presence + 1, 2 * obstacle_definitive_threshold)
            time.sleep(0.5)
        else:
            obstacle_presence = max(obstacle_presence - 1, 0)


        if obstacle_presence > obstacle_definitive_threshold:
            obstacle_presence = 0
            print("obstacle définitif")
            msg = {"obstacle" : True}
            msg["name"] = name
            msg["pos"] = instructions_done
            reqsock.send_pyobj(msg)
            L_deplacement = get_list()
            
            turning = "around"
            turning_around_start_time = time.time()


    # ecoute des messages avec timeout
    i = subsock.poll(timeout=5)
    # s'il y a un message reçu on le traite
    if i != 0:
        msg = subsock.recv_pyobj()
        print("received: {}".format(msg))
        process_msg(msg)
    else:
        # s'il n'y a pas de message on traite le reste des opérations du robot
        if running and obstacle_presence==0:
            motor_command = None
            camera_processor.read(.75)
            
            if turning is not None:
                if turning == 'around':
                    if time.time() - turning_around_start_time < turning_around_timer_threshold:
                        motor_command = (-100, 100)
                        # turning_timer -= 1
                    else:
                        turning = None
                else:
                    if time.time() - turning_start_time < turning_timer_threshold:
                        if turning == "left":
                            motor_command = (-50, 100)
                        elif turning == "right":
                            motor_command = (100, -50)
                    else:
                        turning = None
            elif straight:
                if time.time() - straight_start_time < straight_timer_threshold:
                    deviation = camera_processor.get_deviation()
                        
                    if deviation is not None:
                        motor_command = line_command(deviation)

                else:
                    straight = False
            else:
                if camera_processor.is_in_intersection():
                    intersection_counter = min(intersection_counter + 1, intersection_counter_threshold * 2)
                else:
                    intersection_counter = max(intersection_counter - 1, 0)

                if intersection_counter >= intersection_counter_threshold:
                    turn_instruction = L_deplacement.pop(0)
                    print(turn_instruction)
                    instructions_done +=1
                    
                    if turn_instruction == "left":
                        turning = "left"
                        turning_start_time = time.time()
                        # turning_timer = turning_timer_threshold
                    elif turn_instruction == "right":
                        turning = "right"
                        turning_start_time = time.time()
                        # turning_timer = turning_timer_threshold
                    elif turn_instruction == "straight":
                        straight = True
                        straight_start_time = time.time()
                        # straight_timer = straight_timer_threshold
                    elif turn_instruction == "stop":
                        running = False
                else:
                    deviation = camera_processor.get_deviation()
                
                    if deviation is not None:
                        motor_command = line_command(deviation)

            if motor_command is not None:
                vit_gauche, vit_droite = motor_command
                write_order(serial_file, Order.MOTOR)

                vit_droite = max(-100, min(100, vit_droite))
                vit_gauche = max(-100, min(100, vit_gauche))
                
                write_i8(serial_file, vit_droite)  # vitesse du moteur de droite
                write_i8(serial_file, vit_gauche)  # vitesse du moteur de gauche
            
            #camera_processor.show()
        else:
            write_order(serial_file, Order.MOTOR)
                    
            write_i8(serial_file, 0)  # vitesse du moteur de droite
            write_i8(serial_file, 0)  # vitesse du moteur de gauche
        
