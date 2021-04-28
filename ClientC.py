# -*- coding: utf-8 -*-
"""
Created on Sun Mar 14 15:31:09 2021

@author: lucap

Pour lancer le client, utilisez la commande : python3 ClientC.py localhost:port"""

import sys
from time import sleep
from sys import stdin, exit

from PodSixNet.Connection import connection, ConnectionListener

from tkinter import *
from tkinter import messagebox
from random import *
from math import *

#Constantes
JEU_LARGEUR = 4
JEU_HAUTEUR = 4
CAN_LARGEUR = JEU_LARGEUR*50
CAN_HAUTEUR = JEU_HAUTEUR*50

INITIAL=0
ACTIVE=1
DEAD=-1

#Dictionnaire associant les différents états possible d'un point à une couleur.
COULEUR = {"Sélectionné": 'black', "Neutre": 'grey'}

#Dictionnaire mettant à disposition les facteurs de proportionalités existant 
#entre l'interface graphique et notre jeu divisé en colonnes et lignes.
CONVERSION = {"Pixel largeur": (CAN_LARGEUR/JEU_LARGEUR), "Pixel hauteur": (CAN_HAUTEUR/JEU_HAUTEUR),
              "Colonne": (JEU_LARGEUR/CAN_LARGEUR), "Ligne": (JEU_HAUTEUR/CAN_HAUTEUR)}

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
   
    def Network_tableaux(self, data):
        """Réception des différents tableaux envoyé par le serveur : concernant les points, les lignes,
        et les carrés complétés. Cette fonction appelle ensuite la méthode dessiner."""
        self.jeu.tab = data["tableaux"][0]
        self.jeu.tab_lig = data["tableaux"][1]
        self.jeu.tab_pip = data["tableaux"][2]
        self.jeu.dessiner()
        
    def Network_joueur(self, data):
        """Réception de la data pour savoir qui est le joueur qui doit jouer."""
        self.jeu.joueur = data["joueur"]
        self.jeu.tour.set("Au tour de : " + str(self.jeu.joueur))
        
    def Network_fin(self, data):
        """Création d'une fenêtre en pop-up pour afficher le gagnant de la partie, puis suppression
        de la fenêtre de jeu"""
        gagnant = data["fin"]
        messagebox.showinfo('Partie Terminée', 'Victoire de ' + str(gagnant))
        self.jeu.partie.destroy()
    
    def Network_start(self,data):
        self.state = ACTIVE
        print("started")
   
    def Network_classement(self, data):
        """Réception du classement envoyé par le serveur et appelle
        ensuite la méthode affichage."""
        self.window.classement = data["classement"]
        self.window.affichage()
        
    def Network_combat(self, data):
        """Lance une partie contre un joueur"""
        print("Z'est partiiiiiiiiiiiii !!!!!!!!!")
        self.opposants = data["combat"]
        
        #Récupère le pseudo de l'opposant et lance la partie
        if self.nickname == self.opposants[0]:
            self.window.adversaire = self.opposants[1]
        else:
            self.window.adversaire = self.opposants[0]
        self.jeu = FenetreJeu()

    def Network_error(self, data):
        print('error:', data['error'][1])
        connection.Close()
    
    def Network_disconnected(self, data):
        print('Server disconnected')
        exit()
    

#---------------------------------------------------------------------------------------#

class FenetreRegles(Tk):
    """Fenêtre permettant d'afficher les règles du jeu"""
    
    def __init__(self):
        self.regles = Toplevel(my_window)
        self.regles.title("Règles")
        
        #Définition des labels
        self.nom = Label(self.regles, text = "La Pipopipette un jeu d'anticipations et de stratégies :", wraplength = 500, font=('Helvetica', 15, 'underline'))
        self.titre_regles = Label(self.regles, text = "Règles du jeu :", wraplength = 500, font=('Helvetica', 13, 'italic'),
                                  anchor='w')
        self.regles_du_jeu = Label(self.regles, text = "Le but du jeu est de fermer le plus de carrés possible. " 
                                   + "Le joueur ayant le plus de carré à la fin de la partie gagne, " 
                                   + "c'est à dire que tous les carrés sont occupés. À tour de rôle, "
                                   + "chaque joueur trace un segment entre deux points voisins, en les "
                                   + "selectionnant et en les validant, horizontalement ou verticalement. "
                                   + "Lorsqu’il termine un carré, il y porte sa couleur, puis rejoue. "
                                   + "On peut tracer un segment n’importe où sur la grille.", wraplength = 500,
                                   font=('Helvetica', 12))
        self.titre_conseils = Label(self.regles, text = "Conseils de jeu :", wraplength = 500, font=('Helvetica', 13,'italic'),
                                    anchor='w')
        self.conseils = Label(self.regles, text = "Les traits ne doivent pas forcément partir d’un bord, "
                              + "ni s’enchaîner, le joueur peut placer un trait n’importe où sur la grille. "
                              + "On peut fermer (gagner) un carré même si celui-ci n'a pas été entièrement "
                              + "construit par soi, la possibilité de rejouer après avoir fermé un carré peut "
                              + "être décisive.", wraplength = 500, font=('Helvetica', 12))
        self.nom.pack()
        self.titre_regles.pack()
        self.regles_du_jeu.pack()
        self.titre_conseils.pack()
        self.conseils.pack()
        
        #Définition du bouton permettant de fermer la fenêtre
        bouton_fermer = Button(self.regles, text = "Fermer", command=self.regles.destroy)
        bouton_fermer.pack(side = BOTTOM)


class FenetreJeu(Tk):
    """Fenêtre de la partie en cours"""
    
    def __init__(self):
        self.partie = Toplevel(my_window)
        self.partie.title(str(my_window.client.opposants[0]) + " VS " 
                          + str(my_window.client.opposants[1]))
        
        #Attribution des paramètres des fenêtres
        self.jeu_largeur = JEU_LARGEUR
        self.jeu_hauteur = JEU_HAUTEUR
        self.can_largeur = CAN_LARGEUR
        self.can_hauteur = CAN_HAUTEUR
        
        #Initialisation des différentes variables du jeu 
        self.tab = []
        self.tab_lig =[]
        self.tab_pip=[]
        self.joueur = None
        
        #Création des frames
        self.canva = Canvas(self.partie, width = self.can_largeur, height = self.can_hauteur)
        self.canva.pack(side=LEFT)
        self.partie_affichage = Frame(self.partie)
        self.partie_affichage.pack(side=RIGHT)
        
        #Création des labels affichant le joueur qui doit jouer
        self.pseudo = Label(self.partie_affichage, text = "Vous êtes : " + my_window.client.nickname, font=('Helvetica', 13,'italic'))
        self.pseudo.pack(side=TOP, pady = 15)
        self.tour = StringVar()
        self.tour_lab = Label(self.partie_affichage, textvariable = self.tour, font=('Helvetica', 13,'italic'))
        self.tour.set("Au tour de : " + str(self.joueur))
        self.tour_lab.pack()
        
        #Création du bouton pour abandonner la partie
        self.bouton_abandon = Button(self.partie_affichage,
                                     text="Abandonner", relief = "raised", font=('Helvetica', 13), 
                                     command=lambda:my_window.client.Send({"action" : "abandon",
                                                    "abandon" : [my_window.client.nickname,my_window.adversaire]}))
        self.bouton_abandon.pack(side = BOTTOM, pady = 10)
        
        #Vérifie les clicks de souris dans le plateau de jeu
        self.canva.bind("<ButtonRelease-1>", self.souris)
    
    def souris(self, evt):
        """Récupère les coordonnées de la souris dans le canva, les convertis en coordonnées dans 
        le jeu et l'envoie au serveur."""
        (x,y) = (evt.x, evt.y)
        (i_base,j_base) = (CONVERSION.get("Colonne"), CONVERSION.get("Ligne"))
        (i,j) = (int(x*i_base), int(y*j_base))
        my_window.client.Send({"action" : "souris", "souris" : (i,j)})
            
    def dessiner(self):
        """Fonction permettant de tout afficher sur le plateau de jeu (les points, les
        lignes et les carrés)."""
        (x_base,y_base) = (CONVERSION.get("Pixel largeur"), CONVERSION.get("Pixel hauteur"))
        x_ecart = int((2/10)*x_base)
        y_ecart = int((2/10)*y_base)
        
        #Définit la moitié d'une case pour ensuite pouvoir dessiner au centre d'une case
        DEMI_CARRE_X=(self.can_largeur//self.jeu_largeur)/2
        DEMI_CARRE_Y=(self.can_hauteur//self.jeu_hauteur)/2
        
        #On commence par tout supprimer pour éviter la surcharge 
        self.canva.delete("all")
        
        #Affichage des carrés complétés
        for i in range (len(self.tab_pip)):
            self.canva.create_rectangle(self.tab_pip[i][0],self.tab_pip[i][1],
                                        self.tab_pip[i][2],self.tab_pip[i][3],
                                        fill = self.tab_pip[i][4])
        
        #Parcourt tout le tableau de points pour afficher les points 
        for i in range (self.jeu_largeur):
            for j in range(self.jeu_hauteur):
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

        #Parcourt tout le tableau de lignes pour afficher les lignes tracées
        for numero in range (len(self.tab_lig)):
            (i_t,j_t) = (self.tab_lig[numero][0],self.tab_lig[numero][1])
            if i_t%2 == 0:
                (i_tf,j_tf) = (i_t//2, (j_t-1)//2)
                (x_t1,y_t1)=(x_base*i_tf +DEMI_CARRE_X, y_base*j_tf +DEMI_CARRE_Y)
                (x_t2,y_t2)=(x_base*i_tf +DEMI_CARRE_X, y_base*(j_tf+1) +DEMI_CARRE_Y)
            else :
                (i_tf,j_tf) = ((i_t-1)//2, j_t//2)
                (x_t1,y_t1)=(x_base*i_tf +DEMI_CARRE_X, y_base*j_tf +DEMI_CARRE_Y)
                (x_t2,y_t2)=(x_base*(i_tf+1) +DEMI_CARRE_X, y_base*j_tf +DEMI_CARRE_Y)
            self.canva.create_line(x_t1,y_t1,x_t2,y_t2, fill = 'black')



class FenetreClassement(Tk):
    """Fenêtre affichant le classement du tournoi et permettant de défier un autre joueur"""
    
    def __init__(self, host, port):
        Tk.__init__(self)
        self.client = Client(host, int(port), self)
        self.title(self.client.nickname)
        
        #Attribution des paramètres des fenêtres
        self.classement = []
        self.adversaire = None
        self.choix_adversaire = None
        self.pret = False
        self.partie_classement = Frame(self)
        self.partie_classement.pack(side=TOP)
            
    def affichage(self):
        """Fonction permettant d'afficher le classement (rang, pseudo, score) et les boutons
        pour défier un autre joueur.
        Pour afficher le classement, on utilise la méthode .grid() où l'on précise la ligne et la colonne"""
        #Paramètres de mise en page
        YPAD = 2
        XPAD = 20
        
        #Nettoie la frame en supprimant tous les widgets
        for widget in self.partie_classement.winfo_children():
            widget.destroy()
            
        #Définit et affiche la 1ère ligne du classement
        rang = Label(self.partie_classement, text = "Rang", font=('Helvetica', 13, 'bold'))
        rang.grid(row = 0, column = 0, pady = YPAD, padx = XPAD)
        pseudo = Label(self.partie_classement, text = "Pseudo", font=('Helvetica', 13, 'bold'))
        pseudo.grid(row = 0, column = 1, pady = YPAD, padx = XPAD)
        score = Label(self.partie_classement, text = "Score", font=('Helvetica', 13, 'bold'))
        score.grid(row = 0, column = 2, pady = YPAD, padx = XPAD)
        bouton = Label(self.partie_classement, text = "Choix", font=('Helvetica', 13, 'bold'))
        bouton.grid(row = 0, column = 3, pady = YPAD, padx = XPAD)
        
        #Définit et affiche le classement (rang, pseudo, score, bouton de choix)
        self.var = IntVar()
        for i in range(len(self.classement)):
            rang = Label(self.partie_classement, text = str(self.classement[i][0]), relief = 'raised')
            rang.grid(row = i+1, column = 0, pady = YPAD, padx = XPAD)
            pseudo = Label(self.partie_classement, text = str(self.classement[i][1]))
            pseudo.grid(row = i+1, column = 1, pady = YPAD, padx = XPAD)
            score = Label(self.partie_classement, text = str(self.classement[i][2]))
            score.grid(row = i+1, column = 2, pady = YPAD, padx = XPAD)
            bouton = Radiobutton(self.partie_classement, text = "Challenger " +str(i+1),
                                 variable = self.var, value = i,
                                 command = self.choix)
            bouton.grid(row = i+1, column = 3, pady = YPAD, padx = XPAD)
        
        #Définition des boutons spéciaux ('Quitter' pour quitter, 'Défier' le joueur choisi, 
        #'Règles' pour afficher les règles du jeu).
        bouton_quitter = Button(self.partie_classement, text = "Quitter", command=self.destroy)
        bouton_quitter.grid(row = len(self.classement)+2, column = 0, columnspan = 1, pady = YPAD)
        bouton_defier = Button(self.partie_classement, text = "Defier", command=self.defier)
        bouton_defier.grid(row = len(self.classement)+2, column = 1, columnspan = 2, pady = YPAD)
        bouton_regles = Button(self.partie_classement, text = "Règles", command=self.ouvrir_regles)
        bouton_regles.grid(row = len(self.classement)+2, column = 2, columnspan = 3, pady = YPAD)
        
    def choix(self):
        """Récupère le joueur choisi et vérifie si ce choix est valide (pas soi-même et joueur libre)"""
        rang = self.var.get()
        self.choix_adversaire = self.classement[rang][1]
        if self.choix_adversaire != self.client.nickname or self.classement[rang][3]!= "libre":
            self.pret = True
        else :
            self.pret = False
            
    def defier(self):
        """Si le choix est valide, demande au serveur de lancer le match (le serveur vérifiera si les
        conditions sont valides)"""
        if self.pret:
            print("Moi, " + str(self.client.nickname) + ", je veux défier " + str(self.choix_adversaire))
            self.client.Send({"action" : "duel", "duel" : [self.client.nickname,self.choix_adversaire]})
            
    def ouvrir_regles(self):
        """Ouvre la fenêtre affichant les règles du jeu"""
        fenetre_regle = FenetreRegles()

    def myMainLoop(self):
        while self.client.state!=DEAD: 
            self.update()
            self.client.Loop()
            sleep(0.001)
        exit()


if len(sys.argv) != 2:
    print("Please use: python3", sys.argv[0], "host:port")
    print("e.g., python3", sys.argv[0], "localhost:31425")
    host, port = "localhost", "31425"
else:
    host, port = sys.argv[1].split(":")

my_window = FenetreClassement(host,port)
my_window.myMainLoop()
