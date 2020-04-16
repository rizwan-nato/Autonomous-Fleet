#########################################################################
#
# Enseignement d'intégration ST5 CENTRALESUPELEC
# auteurs : Koen de Turck & Philippe Benabes
# Programme de serveur internet
#
# ce programme reçoit les messages depuis le robot et le controleurng_edges, cmd="start")
# il permet de forwarder les messages depuis le controleur vers les robots
# les messages sont envoyés à tous les robots. Les robots filtrent les messages
# qui leur sont destinés
#
#########################################################################

# import des bibliothèques nécessaires au projet
import zmq
import sys
from path_finding import *

# liste des noeuds connectés au serveur
nodes = {}
# adresse IP du serveur
ip = "192.168.137.53"
ip_input = input("ip server : ")
if ip_input != "":
    ip = ip_input

if len(sys.argv) > 1:
    ip = sys.argv[1]

# connection pour recevoir les messages depuis robot et controleur
ctx = zmq.Context()
repaddr = "tcp://{}:5005".format(ip)
repsock = ctx.socket(zmq.REP)
repsock.bind(repaddr)

# connection pour publier les messages à tous les robots
pubaddr = "tcp://{}:6006".format(ip)
pubsock = ctx.socket(zmq.PUB)
pubsock.bind(pubaddr)

# init mapping graph
waze = Graph()


Destination = {"bot001" : (2, 2)}

#############################################
# procedure pour répondre aux messages reçus
#############################################
def process_msg(msg):
    reply = {"all": "is fine"}
    ##################################################
    # réponse à la première connection de chaque robot
    ##################################################
    if "from" in msg and msg["from"] not in nodes:
        print("new node signing in, adding {} to nodes".format(msg["from"]))
        nodes[msg["from"]] = ""

    ###################################################################################
    # réponse à la demande nodelist -> renvoie la liste des objets connectés au serveur
    ###################################################################################
    if "nodelist" in msg:
        reply["nodelist"] = list(nodes.keys())

    ##################################################################################
    # réponse à une demande de forward -> le message est publié à tous les robots
    ##################################################################################
    if "from" in msg and msg["from"] == "controller" and "msg" in msg and "forward_to" in msg:
        print("forwarding a controller msg to ", msg["forward_to"])
        msg1 = msg["msg"]
        msg1["to"] = msg["forward_to"]
        pubsock.send_pyobj(msg1)

    ###################################################################
    #  réponse a une requete
    ###################################################################
    if "request" in msg:
        print("the bot has a request")
        reply = {"all": "is fine"}

    #####################################################################
    # réponse à un message d'information du robot
    #####################################################################
    if "obstacle" in msg:
        if msg["obstacle"] == True:
            robot = msg["name"]
            end_point = Destination[robot]
            instructions_done = msg["pos"]
            pos = waze.where_am_i(robot, instructions_done)
            last_pos = waze.where_am_i(robot,instructions_done-1)
            waze.add_obstacle(pos, last_pos)
            L = waze.cross_planning(pos, end_point,robot)
            print(L)
            reply = {"to": robot}
            reply["deplacement"] = L


    if "deplacement" in msg:
        if msg["deplacement"] == "send":
            robot = msg["name"]
            end_point = Destination[robot]
            start_point = msg["start"]
            L = waze.cross_planning(start_point, end_point,robot)
            print(L)
            reply = {"to": robot}
            reply["deplacement"] = L

    # renvoie le message de réponse 
    return reply


## Liste initiale des déplacement à faire

###############################################################
# boucle de réception des messages et transmission des réponses
###############################################################

while True:
    # reception du message
    msg = repsock.recv_pyobj()
    # print("received: {}".format(msg))

    # calcul de la réponse
    reply = process_msg(msg)
    # print("reply: {}".format(reply))

    # transmission de la réponse aux robots
    repsock.send_pyobj(reply)
