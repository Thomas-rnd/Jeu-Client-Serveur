# -*- coding: utf-8 -*-
"""
Created on Sun Mar 14 15:31:07 2021

@author: lucap
"""

import sys
from time import sleep, localtime
from PodSixNet.Server import Server
from PodSixNet.Channel import Channel
from tkinter import *
from random import *
from math import *

#Constantes
JEU_LARGEUR = 3
JEU_HAUTEUR = 3
CAN_LARGEUR = 150
CAN_HAUTEUR = 150

#Dictionnaire associant les différents états possible d'un point à une couleur.
COULEUR = {"Sélectionné": 'black', "Neutre": 'grey', "Appartient au joueur 1": 'red',
               "Appartient au joueur 2": 'blue'}

#Dictionnaire mettant à disposition les facteurs de proportionalités existant 
#entre l'interface graphique et notre jeu divisé en colonnes et lignes.
CONVERSION = {"Pixel largeur": CAN_LARGEUR/JEU_LARGEUR, "Pixel hauteur": CAN_HAUTEUR/JEU_HAUTEUR,
              "Colonne": JEU_LARGEUR/CAN_LARGEUR, "Ligne": JEU_HAUTEUR/CAN_HAUTEUR}

"""Pour lancer le serveur, utilisez la commande : python3 TD4Serveur.py localhost:port"""

##################################################################################################
##################################################################################################
########################                    LE JEU                     ###########################
##################################################################################################
##################################################################################################


class JeuPipopipette():
    """Gère le système de jeu, règles du jeu, création de saucisses, recommencer une 
    partie et abandonner."""  
    def __init__(self):
        self.nbr_colonne = JEU_LARGEUR
        self.nbr_ligne = JEU_HAUTEUR
        self.joueur = 0
        self.score1 = 0
        self.score2 = 0
        self.recommencer()
          
    def recommencer(self):
        """Réinitialise le tableau contenant les etats de tous les points et croisements 
        du plateau de jeu."""
        self.tableau_point = []
        self.tableau_carré=[]
        self.tableau_ligne=[]
        for i in range (self.nbr_colonne):
            ligne = []
            for j in range (self.nbr_ligne):
                    ligne.append('Neutre')
            self.tableau_point.append(ligne)
    
    def changer_etat(self, action, i, j):
        """Permet de changer l'état d'un point (pour l'état sélectioné ou validé) et 
        d'un croissement pour l'état vide ou occupé.""" 
        etat = self.tableau_point[i][j]
        if action == 'selection':
            if etat == 'Neutre':
                etat = 'Sélectionné'
            elif etat == 'Sélectionné':
                etat = 'Neutre'
            
        elif action == 'validation':
            etat = 'Neutre'

        self.tableau_point[i][j]=etat
    
    def creer_trait(self, liste):
        """Ajout des coordonnées d'une saucisse dans le tableau lignes"""
        DEMI_CARRE_X=(CAN_LARGEUR//self.nbr_colonne)/2
        DEMI_CARRE_Y=(CAN_HAUTEUR//self.nbr_ligne)/2
        (COL,LIG) = (0,1)
        (x_base,y_base) = (CONVERSION.get("Pixel largeur"),CONVERSION.get("Pixel hauteur"))
        
        #Parcourt la liste de points donnée en entrée et ajoute les coordonnées des lignes
        #entre chaque point et son suivant (la couleur dépend du joueur qui joue)
        for i in range (len(liste)-1):
            (x1,y1)=(x_base*liste[i][COL], y_base*liste[i][LIG])
            (x2,y2)=(x_base*liste[i+1][COL], y_base*liste[i+1][LIG])
            trait = [x1+DEMI_CARRE_X,y1+DEMI_CARRE_Y,
                     x2+DEMI_CARRE_X,y2+DEMI_CARRE_Y, 'black']
            for ligne in self.tableau_ligne :
                if ligne == trait :
                    return None
                
        self.tableau_ligne.append(trait)
        return ("OK")

    def accessible(self,liste):
        """Vérifie si les points sélectionnés en noir peuvent être une saucisse
        (3 points côte à côte et pas de croissement)."""   
        NORME = CAN_LARGEUR//JEU_LARGEUR
        norme = 0
        (COL,LIG) = (0,1)
        (x_base,y_base) = (CONVERSION.get("Pixel largeur"),CONVERSION.get("Pixel hauteur"))
        
        #Parcourt la liste de point donnée en entrée et ajoute la norme de la distance
        #entre chaque point dans une liste
        for i in range (len(liste)-1):
            (x1,y1)=(x_base*liste[i][COL],y_base*liste[i][LIG])
            (x2,y2)=(x_base*liste[i+1][COL],y_base*liste[i+1][LIG])
            norme = sqrt(((x2-x1)**2)+((y2-y1)**2))
        if norme != NORME : 
            return None
        
        return (liste)
    
    
##################################################################################################
##################################################################################################
########################                  LE SERVEUR                   ###########################
##################################################################################################
##################################################################################################
    
class ClientChannel(Channel):
    """."""
    def __init__(self, *args, **kwargs):
        self.nickname = "anonymous"
        Channel.__init__(self, *args, **kwargs)
    
    def Close(self):
        self._server.DelPlayer(self)
        
    def Network_souris(self, data):
        """Après avoir reçu les coordonnées d'un point, lui change son état puis
        envoie le tableau avec les états mis à jour."""
        print(data)
        
        #Si le joueur qui a cliqué n'est pas celui qui doit jouer, rien ne se passe
        who = self.nickname
        if who != self._server.liste_joueurs[jeu.joueur]:
            return
        
        (i,j) = data["souris"]
        jeu.changer_etat("selection", i, j)
        self._server.SendToEveryone("tableau", {"tableau": jeu.tableau_point})
        
    def Network_valid(self, data):
        """Verifie si le bon joueur joue, change l'état des points et des croissements
        ainsi que le tour des joueurs. Après cela toutes ces informations sont envoyées
        aux différents clients."""
        print(data)
        
        #Si le joueur qui a cliqué n'est pas celui qui doit jouer ou s'il n'y a pas
        #d'adversaire, rien ne se passe
        who = self.nickname
        if len(self._server.liste_joueurs)<2 or who != self._server.liste_joueurs[jeu.joueur]:
            return
        
        #Récupère la liste de points validés et les croisements associés pour changer leur état
        liste = jeu.accessible(data["valid"])
        if liste is None:
            return
        if jeu.creer_trait(liste) is None :
            return
            
        for pt in liste:
            jeu.changer_etat('validation', pt[0], pt[1])   
        
        #Change le joueur qui doit jouer
        if jeu.joueur == 0 :
            jeu.joueur = 1
        else :
            jeu.joueur = 0
        
        #Crée une saucisse avec les points validés et envoie toutes les infos aux joueurs
        self._server.SendToEveryone("tableau", {"tableau" : jeu.tableau_point})
        self._server.SendToEveryone("tableau_ligne", {"tableau_ligne" : jeu.tableau_ligne})      
        self._server.SendToEveryone("joueur", {"joueur" : self._server.liste_joueurs[jeu.joueur]})
    
    def Network_nickname(self, data):
        """Récupère le pseudo des joueurs et les met dans une liste (liste_joueurs)."""
        self.nickname = data["nickname"]
        self._server.liste_joueurs.append(self.nickname)
        self._server.PrintPlayers()
        self.Send({"action" : "start"})
        self.Send({"action" : "joueur", "joueur" : self._server.liste_joueurs[jeu.joueur]})  
   
                                           
class MyServer(Server):
    channelClass = ClientChannel
    
    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.players = {}
        self.liste_joueurs = []
        print('Server launched')
    
    def Connected(self, channel, addr):
        self.AddPlayer(channel)
    
    def AddPlayer(self, player):
        """Quand une nouvelle personne se connecte au serveur le tableau de point et 
        le tableau avec toutes les saucisses lui est envoyé."""
        print("New Player connected")
        self.players[player] = True
        player.Send({"action" : "tableau", "tableau" : jeu.tableau_point})
        player.Send({"action" : "tableau_ligne", "tableau_ligne" : jeu.tableau_ligne})
 
    def PrintPlayers(self):
        print("players' nicknames :", [p.nickname for p in self.players])
  
    def DelPlayer(self, player):
        print("Deleting Player " + player.nickname + " at "+str(player.addr))
        self.liste_joueurs.remove(player.nickname)
        del self.players[player]
       
    def SendToOthers(self, data):
        """Fonction permettant d'envoyer la data à tous les joueurs sauf au jouer qui joue."""
        [p.Send({"action" : "tableau", "tableau" : data["tableau"]}) for p in self.players 
                                                                     if p.nickname != data["who"]]
    
    def SendToEveryone(self, nom, data):
        """Fonction permettant d'envoyer la data à tous les joueurs."""
        [p.Send({"action": nom, nom : data[nom]}) for p in self.players]
    
    def Launch(self):
        while True:
            self.Pump()
            sleep(0.001)


# get command line argument of server, port
if len(sys.argv) != 2:
    print("Please use: python3", sys.argv[0], "host:port")
    print("e.g., python3", sys.argv[0], "localhost:31425")
    host, port = "localhost","31425"
else:
    host, port = sys.argv[1].split(":")

s = MyServer(localaddr=(host, int(port)))
jeu = JeuPipopipette()
s.Launch()
