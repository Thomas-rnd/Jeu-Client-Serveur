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
JEU_LARGEUR = 11
JEU_HAUTEUR = 9
CAN_LARGEUR = 550
CAN_HAUTEUR = 450

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


class JeuSaucisse():
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
        self.tableau = []
        self.tableau_ligne=[]
        for i in range (self.nbr_colonne):
            ligne = []
            for j in range (self.nbr_ligne):
                if (i+j)%2==0:
                    ligne.append('Neutre')
                else :
                    ligne.append('croisement vide')
            self.tableau.append(ligne)
    
    def changer_etat(self, action, i, j):
        """Permet de changer l'état d'un point (pour l'état sélectioné ou validé) et 
        d'un croissement pour l'état vide ou occupé.""" 
        etat = self.tableau[i][j]
        if action == 'selection':
            if etat == 'Neutre':
                etat = 'Sélectionné'
            elif etat == 'Sélectionné':
                etat = 'Neutre'
            elif etat == 'croisement vide':
                etat = 'croisement occupe'
            
        elif action == 'validation':
            if self.joueur == 0:
                etat = 'Appartient au joueur 1'
            elif self.joueur == 1:
                etat = 'Appartient au joueur 2'
        
        self.tableau[i][j]=etat
    
    def creer_saucisse(self, liste):
        """Ajout des coordonnées d'une saucisse dans le tableau lignes"""
        DEMI_CARRE_X=(CAN_LARGEUR//self.nbr_colonne)/2
        DEMI_CARRE_Y=(CAN_HAUTEUR//self.nbr_ligne)/2
        (COL,LIG) = (0,1)
        (x_base,y_base) = (CONVERSION.get("Pixel largeur"),CONVERSION.get("Pixel hauteur"))
        
        #Parcourt la liste de points donnée en entrée et ajoute les coordonnées des lignes
        #entre chaque point et son suivant (la couleur dépend du joueur qui joue)
        for i in range (len(liste)-1):
            if self.joueur == 0:
                (x1,y1)=(x_base*liste[i][COL], y_base*liste[i][LIG])
                (x2,y2)=(x_base*liste[i+1][COL], y_base*liste[i+1][LIG])
                self.tableau_ligne.append([x1+DEMI_CARRE_X,y1+DEMI_CARRE_Y,
                                           x2+DEMI_CARRE_X,y2+DEMI_CARRE_Y, 'blue'])
            else : 
                (x1,y1)=(x_base*liste[i][COL],y_base*liste[i][LIG])
                (x2,y2)=(x_base*liste[i+1][COL],y_base*liste[i+1][LIG])
                self.tableau_ligne.append([x1+DEMI_CARRE_X, y1+DEMI_CARRE_Y,
                                           x2+DEMI_CARRE_X, y2+DEMI_CARRE_Y, 'red'])

    def accessible(self,liste):
        """Vérifie si les points sélectionnés en noir peuvent être une saucisse
        (3 points côte à côte et pas de croissement)."""   
        NORME = (CAN_LARGEUR//JEU_LARGEUR)*2
        norme = []
        (COL,LIG) = (0,1)
        (x_base,y_base) = (CONVERSION.get("Pixel largeur"),CONVERSION.get("Pixel hauteur"))
        
        #Parcourt la liste de point donnée en entrée et ajoute la norme de la distance
        #entre chaque point dans une liste
        for i in range (len(liste)-1):
            (x1,y1)=(x_base*liste[i][COL],y_base*liste[i][LIG])
            (x2,y2)=(x_base*liste[i+1][COL],y_base*liste[i+1][LIG])
            norme.append(sqrt(((x2-x1)**2)+((y2-y1)**2)))
        
        (x_init,y_init)=(x_base*liste[0][COL],y_base*liste[0][LIG])
        (x_fin,y_fin)=(x_base*liste[len(liste)-1][COL],
                       y_base*liste[len(liste)-1][LIG])
        norme.append(sqrt(((x_fin-x_init)**2)+((y_fin-y_init)**2)))
        
        #Si une norme est trop grande (points trop espacés), la liste de point est 
        #réordonnée et la norme est supprimée de la liste des normes
        erreur = []
        for i in range(len(norme)):
            if norme[i] > NORME:
                if i != len(norme)-1:
                    liste.append(liste.pop(i+1))
                    liste.insert(0,liste.pop(i))
                erreur.insert(0,i)
        for i in erreur:
            norme.pop(i)
        
        #Si la liste de norme contient moins de 2 normes, c'est que les points sont trop espacés
        if len(norme)<=1:
            return (None,None)
        
        #Parcourt la liste de point (dorénavant ordonnée) et si 2 points sont sur une
        #même colonne/ligne, vérifie s'il y a un croisement puis change son état
        croisement = []
        for i in range (len(liste)-1):
            (i1,j1)=(liste[i][COL],liste[i][LIG])
            (i2,j2)=(liste[i+1][COL],liste[i+1][LIG])
            if i1==i2 or j1==j2:
                (ic,jc) = ((i1+i2)//2,(j1+j2)//2)
                if self.tableau[ic][jc] == 'croisement occupe':
                    return (None,None)
                else :
                    croisement.append([ic,jc])
        return (liste,croisement)
    
    
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
        self._server.SendToEveryone("tableau", {"tableau": jeu.tableau})
        
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
        (liste,croisement) = jeu.accessible(data["valid"])
        if liste is None:
            return
        for pt in liste:
            jeu.changer_etat('validation', pt[0], pt[1])   
        for cr in croisement:
            jeu.changer_etat('selection', cr[0], cr[1])
        
        #Change le joueur qui doit jouer
        if jeu.joueur == 0 :
            jeu.joueur = 1
        else :
            jeu.joueur = 0
        
        #Crée une saucisse avec les points validés et envoie toutes les infos aux joueurs
        jeu.creer_saucisse(liste)
        self._server.SendToEveryone("tableau", {"tableau" : jeu.tableau})
        self._server.SendToEveryone("tableau_ligne", {"tableau_ligne" : jeu.tableau_ligne})      
        self._server.SendToEveryone("joueur", {"joueur" : self._server.liste_joueurs[jeu.joueur]})
    
    def Network_nickname(self, data):
        """Récupère le pseudo des joueurs et les met dans une liste (liste_joueurs)."""
        self.nickname = data["nickname"]
        self._server.liste_joueurs.append(self.nickname)
        self._server.PrintPlayers()
        self.Send({"action" : "start"})
        self.Send({"action" : "joueur", "joueur" : self._server.liste_joueurs[jeu.joueur]})
    
    def Network_abandon(self, data):
        """Augmente le score du joueur qui n'a pas abandonner et réinitialisele plateau de jeu."""
        
        #Si le joueur qui a cliqué n'est pas celui qui doit jouer ou s'il n'y a pas
        #d'adversaire, rien ne se passe
        who = self.nickname
        if len(self._server.liste_joueurs)<2 or who != self._server.liste_joueurs[jeu.joueur]:
            return
        
        #Change le score en fonction du joueur qui a abandonné
        if jeu.joueur == 0 :
            jeu.score2 += 1
        else :
            jeu.score1 += 1
            
        #Réinitialise le plateau de jeu et envoie toutes les infos aux joueurs
        jeu.recommencer()
        self._server.SendToEveryone("tableau", {"tableau" : jeu.tableau})
        self._server.SendToEveryone("tableau_ligne", {"tableau_ligne" : jeu.tableau_ligne}) 
        self._server.SendToEveryone("score", {"score" : [(jeu.score1,jeu.score2),
                                                         (self._server.liste_joueurs[0],
                                                          self._server.liste_joueurs[1])]})

                                              
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
        player.Send({"action" : "tableau", "tableau" : jeu.tableau})
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
jeu = JeuSaucisse()
s.Launch()
