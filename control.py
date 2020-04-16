#########################################################################
#
# Enseignement d'intégration ST5 CENTRALESUPELEC
# auteurs : Koen de Turck & Philippe Benabes
# Programme de client de controle et d'interface homme machine
#
# ce programme sert d'interface homme machine et permet d'envoyer des
# messages au robot via le serveur
#
#########################################################################

# import des bibliothèques nécessaires au projet
import zmq
# import msvcrt
import getch
import time

ctx, addr, sock = 3 * [None]
# n° d'IP du serveur
ip = "192.168.137.32"
ip_input = input("ip server : ")
if ip_input != "":
    ip = ip_input


# procedure de connexion au serveur
def start(ip=ip):
    global ctx, addr, sock
    ctx = zmq.Context()
    addr = "tcp://{}:5005".format(ip)
    sock = ctx.socket(zmq.REQ)
    sock.connect(addr)


# procedure de récupération des noms des clients connectés au serveur
def get_nodes():
    print('sending botlist request to server @ {} ...'.format(addr))
    sock.send_pyobj({"from": "controller", "nodelist": ""})
    msg = sock.recv_pyobj()
    return msg["nodelist"]


# procedure pour forwarder un message à un robot via le serveur
def forward_msg(bot, msg):
    print('relaying msg to bot {} via server @ {} ...'.format(bot, addr))
    sock.send_pyobj({"from": "controller", "forward_to": bot, "msg": msg})
    msg = sock.recv_pyobj()
    return msg


######################################################
#
# programme principal
#
######################################################

# connexion au serveur
start()

# variable indiquant quand il faut afficher le message d'accueil
endcmd = 1
while True:
    if (endcmd):
        #
        # affichage du message d'accueil de l'IHM
        # après chaque appui de touche
        #
        print("\nProgramme principal");
        print("Robots disponibles", get_nodes());
        print("A,Q -> Lancement du robot 1,2")
        print("E,D -> Arret du robot 1,2 ")
        print("Z,S -> Envoyer la destination du robot 1,2")
        print("Entrez votre commande")
        endcmd = 0

    #
    # detection de l'appui d'une touche sur le clavier
    #
    command = getch.getche()
    #
    # traitement des commandes clavier
    #
    if (command == 'a' or command == 'A'):
        # envoi d'une commande start au robot bot1
        msg = {"command": "start"}
        forward_msg("bot001", msg)
    if (command == 'q' or command == 'Q'):
        # envoi d'une commande start au robot bot2
        msg = {"command": "start"}
        forward_msg("bot002", msg)
    if (command == 'e' or command == 'E'):
        # envoi d'une commande stop au robot bot1
        msg = {"command": "stop"}
        forward_msg("bot001", msg)
    if (command == 'd' or command == 'D'):
        # envoi d'une commande stop au robot bot2
        msg = {"command": "stop"}
        forward_msg("bot002", msg)
    if (command == 'z' or command == 'Z'):
        # demande adresse
        x = input('\nx bot1 : ')
        y = input('y bot1 : ')
        # envoi d'une destination au robot bot1
        msg = {"dest": (x, y)}
        forward_msg("bot001", msg)
    if (command == 's' or command == 'S'):
        # demande adresse
        x = input('\nx bot2 : ')
        y = input('y bot2 : ')
        # envoi d'une destination au robot bot1
        msg = {"dest": (x, y)}
        forward_msg("bot002", msg)

    endcmd = 1
