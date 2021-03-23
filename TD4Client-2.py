# -*- coding: utf-8 -*-
"""
Created on Sun Mar 14 15:31:09 2021

@author: lucap
"""#hey

import sys
from time import sleep
from sys import stdin, exit

from PodSixNet.Connection import connection, ConnectionListener

from tkinter import *
from random import *
from math import *

#Constantes
JEU_LARGEUR = 11
JEU_HAUTEUR = 9
CAN_LARGEUR = 550
CAN_HAUTEUR = 450

INITIAL=0
ACTIVE=1
DEAD=-1

#Dictionnaire associant les différents états possible d'un point à une couleur.
COULEUR = {"Sélectionné": 'black', "Neutre": 'grey', "Appartient au joueur 1": 'red',
               "Appartient au joueur 2": 'blue'}

#Dictionnaire mettant à disposition les facteurs de proportionalités existant 
#entre l'interface graphique et notre jeu divisé en colonnes et lignes.
CONVERSION = {"Pixel largeur": (CAN_LARGEUR/JEU_LARGEUR), "Pixel hauteur": (CAN_HAUTEUR/JEU_HAUTEUR),
              "Colonne": (JEU_LARGEUR/CAN_LARGEUR), "Ligne": (JEU_HAUTEUR/CAN_HAUTEUR)}

"""Pour lancer le client, utilisez la commande : python3 TD4Client.py localhost:port"""

#---------------------------------------------------------------------------------------#

class Client(ConnectionListener):
    """Cette classe va nous permettre de recupérer toutes les informations importantes 
    lors de l'avancement d'une partie."""
    
    def __init__(self, host, port, window):
        self.window = window
        self.Connect((host, port))
        self.state=INITIAL
        print("Client started")
        print("Ctrl-C to exit")
        print("Enter your nickname: ")
        nickname=stdin.readline().rstrip("\n")
        self.nickname = nickname
        connection.Send({"action" : "nickname", "nickname" : nickname})

    def Network_connected(self, data):
        print("You are now connected to the server")
    
    def Loop(self):
        connection.Pump()
        self.Pump()

    def quit(self):
        self.window.destroy()
        self.state=DEAD
   
    def Network_start(self,data):
        self.state = ACTIVE
        print("started")
   
    def Network_tableau(self, data):
        """Reception du tableau de points envoyé par le serveur et appelle
        ensuite la méthode dessiner."""
        self.window.tab = data["tableau"]
        self.window.dessiner()
        
    def Network_tableau_ligne(self, data):
        """Reception du tableau (regroupant toutes les saucisses) envoyé par 
        le serveur et appelle la méthode dessiner."""
        self.window.tab_lig = data["tableau_ligne"]
        self.window.dessiner()
        
    def Network_joueur(self, data):
        """Reception de la data pour savoir qui est le joueur qui doit jouer."""
        self.window.joueur = data["joueur"]
        self.window.tour.set("Au tour de : " + str(self.window.joueur))
        
    def Network_score(self, data):
        """Reception de la data pour savoir le score actuel ainsi que les pseudos des
        2 joueurs qui sont en train de jouer"""
        (self.window.score_joueur1, self.window.score_joueur2) = data["score"][0]
        (self.window.adversaire1, self.window.adversaire2) = data["score"][1]
        self.window.score1.set("Score de {} : ".format(self.window.adversaire1) + str(self.window.score_joueur1))
        self.window.score2.set("Score de {} : ".format(self.window.adversaire2) + str(self.window.score_joueur2))
    
    def Network_error(self, data):
        print('error:', data['error'][1])
        connection.Close()
    
    def Network_disconnected(self, data):
        print('Server disconnected')
        exit()
    

#---------------------------------------------------------------------------------------#


class Fenetre(Tk):
    """Gère la fenêtre de jeu des clients, en affichant tout ce qui est necessaire."""
    
    def __init__(self, host, port):
        Tk.__init__(self)
        self.client = Client(host, int(port), self)
        
        #Attribution des paramètres des fenêtres
        self.delai       = 250
        self.jeu_largeur = JEU_LARGEUR
        self.jeu_hauteur = JEU_HAUTEUR
        self.can_largeur = CAN_LARGEUR
        self.can_hauteur = CAN_HAUTEUR
        self.tab = []
        self.tab_lig =[]
        self.joueur = None
        self.score_joueur1 = 0
        self.score_joueur2= 0
        self.adversaire1 = None
        self.adversaire2 = None
        
        #Création des fenêtre et lancement du jeu
        self.canva = Canvas(self, width = self.can_largeur, height = self.can_hauteur)
        self.canva.pack(side=LEFT)
        self.partie_affichage = Frame(self)
        self.partie_affichage.pack(side=RIGHT)
        
        #Création du label affichant le joueur qui doit jouer et les scores
        self.pseudo = Label(self.partie_affichage, text = "Vous êtes : " + self.client.nickname)
        self.pseudo.pack(side=TOP, pady = 15)
        self.tour = StringVar()
        self.tour_lab = Label(self.partie_affichage, textvariable = self.tour)
        self.tour.set("Au tour de : " + str(self.joueur))
        self.tour_lab.pack()
        self.score1 = StringVar()
        self.score1_lab = Label(self.partie_affichage, textvariable = self.score1)
        self.score1.set("Score du Joueur 1 : " + str(self.score_joueur1))
        self.score1_lab.pack()
        self.score2 = StringVar()
        self.score2_lab = Label(self.partie_affichage, textvariable = self.score2)
        self.score2.set("Score du Joueur 2 : " + str(self.score_joueur2))
        self.score2_lab.pack()
        
        #Création des boutons
        self.bouton_valider = Button(self.partie_affichage,
                                  text="Valider", command=self.validation)
        self.bouton_quitter = Button(self.partie_affichage,
                                     text="Quitter", command=self.destroy)
        self.bouton_quitter.pack(side = BOTTOM, pady = 10)
        self.bouton_valider.pack(pady = 10)
        self.bouton_abandon=Button(self.partie_affichage, text= 'Abandonner',
                                   command = lambda : self.client.Send({"action" : "abandon" }))
        self.bouton_abandon.pack(pady = 10)
        
        #Vérifie les clicks de souris et lance la boucle maj
        self.canva.bind("<ButtonRelease-1>", self.souris)
    
    def souris(self, evt):
        """Récupère les coordonnées de la souris dans le canva, les convertit dans le 
        jeu et l'envoie au serveur."""
        (x,y) = (evt.x, evt.y)
        (i_base,j_base) = (CONVERSION.get("Colonne"), CONVERSION.get("Ligne"))
        (i,j) = (int(x*i_base), int(y*j_base))
        self.client.Send({"action" : "souris", "souris" : (i,j)})
    
    def validation(self):
        """Vérifie s'il y a 3 points en noir, puis envoie la liste de points noirs au
        serveur qui vérifiera si les points sont valides"""
        
        #Fais une liste regroupant les points sélectionnés (noir)
        liste_pt_noir = []
        for i in range (self.jeu_largeur):
            for j in range(self.jeu_hauteur):
                if self.tab[i][j] == 'Sélectionné':
                    liste_pt_noir.append([i,j])
        
        #Si 3 points sélectionnés, cette liste est envoyée au serveur pour être 
        #vérifiée
        if len(liste_pt_noir) == 3:
            self.client.Send({"action" : "valid", "valid" : liste_pt_noir})
            
    def dessiner(self):
        """Fonction permettant de tout afficher sur le plateau de jeu (les points, les
        saucisses)."""
        (x_base,y_base) = (CONVERSION.get("Pixel largeur"), CONVERSION.get("Pixel hauteur"))
        x_ecart = int((2/10)*x_base)
        y_ecart = int((2/10)*y_base)
        self.canva.delete("all")
        
        # Parcourt tout le tableau de point pour afficher les points
        for i in range (self.jeu_largeur):
            for j in range(self.jeu_hauteur):
                if (i+j)%2 == 0:
                    (x1,y1) = (int(i*x_base), int(j*y_base))
                    (x2,y2) = (int((i+1)*x_base), int((j+1)*y_base))
                    if self.tab[i][j] == 'Neutre':
                        self.canva.create_oval(x1+x_ecart,y1+y_ecart,
                                               x2-x_ecart,y2-y_ecart,
                                               fill=COULEUR.get(self.tab[i][j]))
                    elif self.tab[i][j] == 'Sélectionné':
                        self.canva.create_oval(x1+x_ecart,y1+y_ecart,
                                               x2-x_ecart,y2-y_ecart,
                                               fill=COULEUR.get(self.tab[i][j]))
                    elif self.tab[i][j] == 'Appartient au joueur 1':
                        self.canva.create_oval(x1+x_ecart,y1+y_ecart,
                                               x2-x_ecart,y2-y_ecart,
                                               fill=COULEUR.get(self.tab[i][j]))
                    elif self.tab[i][j] == 'Appartient au joueur 2':
                        self.canva.create_oval(x1+x_ecart,y1+x_ecart,
                                               x2-x_ecart,y2-y_ecart,
                                               fill=COULEUR.get(self.tab[i][j])) 

        #Parcourt tout le tableau de ligne pour afficher les lignes
        for i in range (len(self.tab_lig)):
            self.canva.create_line(self.tab_lig[i][0],self.tab_lig[i][1],
                                   self.tab_lig[i][2],self.tab_lig[i][3],
                                  fill=self.tab_lig[i][4])
            
    def myMainLoop(self):
        while self.client.state!=DEAD: 
            self.update()
            self.client.Loop()
            sleep(0.001)
        exit()


# get command line argument of client, port
if len(sys.argv) != 2:
    print("Please use: python3", sys.argv[0], "host:port")
    print("e.g., python3", sys.argv[0], "localhost:31425")
    host, port = "localhost", "31425"
else:
    host, port = sys.argv[1].split(":")

my_window = Fenetre(host,port)
my_window.myMainLoop()