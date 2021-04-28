# -*- coding: utf-8 -*-
"""
Created on Sun Mar 14 15:31:07 2021

@author: lucap

------------------------ A faire ------------------------

Optionnel : 
    - Coder les contraintes d'affrontement (demande si diff grande)
    - Afficher sur le tableau quel joueur est en match (couleur)
    
---------------------------------------------------------

Pour lancer le serveur, utilisez la commande : python3 ServeurC.py localhost:port"""

import sys
from time import sleep, localtime
from PodSixNet.Server import Server
from PodSixNet.Channel import Channel
from tkinter import *
from random import *
from math import *

#Constantes
JEU_LARGEUR = 4
JEU_HAUTEUR = 4
CAN_LARGEUR = JEU_LARGEUR*50
CAN_HAUTEUR = JEU_HAUTEUR*50

#Dictionnaire mettant à disposition les facteurs de proportionalités existant 
#entre l'interface graphique et notre jeu divisé en colonnes et lignes.
CONVERSION = {"Pixel largeur": CAN_LARGEUR/JEU_LARGEUR, "Pixel hauteur": CAN_HAUTEUR/JEU_HAUTEUR,
              "Colonne": JEU_LARGEUR/CAN_LARGEUR, "Ligne": JEU_HAUTEUR/CAN_HAUTEUR}

#Fonction de tri dans l'ordre décroissant utilisée pour ordonner les joueurs selon leur score
def tri_insertion(L):
    L2 = []
    L2.insert(0,L[0])
    for i in range (1,len(L)):
        pos = 0
        while pos<len(L2) and L[i][2]<L2[pos][2]:
            pos = pos + 1
        L2.insert(pos,L[i])
    return L2

##################################################################################################
##################################################################################################
########################                    LE JEU                     ###########################
##################################################################################################
##################################################################################################


class Tournoi():
    """Gère le tournoi : le classement, les affrontements, les scores..."""
    
    def __init__(self):
        """Initialise un tableau pour le classement et une liste pour les différents plateaux de jeu"""
        self.tab_cla = []
        self.plateaux = []
        
    def maj_cla(self, action, info = None):
        """Permet de mettre à jour différents paramètres du tournoi"""
        
        if action == "Etat":
            #Obectif : Changer l'état de 2 joueurs et d'un plateau (début ou fin de match)
            (pseudo_1,pseudo_2,num_plateau) = info
            
            #Récupère la position dans le tableau des 2 joueurs
            for i in range (len(self.tab_cla)):
                if pseudo_1 == self.tab_cla[i][1] :
                    placement_1 = i
                if pseudo_2 == self.tab_cla[i][1] :
                    placement_2 = i
            
            #Change l'état en fonction de si le match est lancé ou terminé
            if self.tab_cla[placement_1][3] == "libre":
                self.tab_cla[placement_1][3] = num_plateau
                self.tab_cla[placement_2][3] = num_plateau
                self.plateaux[num_plateau][1] = "occupe"
            else :
                self.tab_cla[placement_1][3] = "libre"
                self.tab_cla[placement_2][3] = "libre"
                self.plateaux[num_plateau][1] = "libre"
                
        if action == "Resultat":
            #Objectif : Mettre à jour les scores et le classement à l'issue d'un match
            (gagnant, perdant) = info
            
            #Récupère la position des 2 joueurs dans le tableau
            for i in range (len(self.tab_cla)):
                if gagnant == self.tab_cla[i][1] :
                    placement_g = i
                if perdant == self.tab_cla[i][1] :
                    placement_p = i
            
            #Change les scores du gagnant et du perdant et tri le tableau
            ecart = (1/3)*(self.tab_cla[placement_g][2] - self.tab_cla[placement_p][2])
            self.tab_cla[placement_g][2] += (100 - int(ecart))
            self.tab_cla[placement_p][2] -= (100 - int(ecart))
            Lbis = tri_insertion(self.tab_cla)
            
            #Met à jour le rang des joueurs et attribut le nouveau classement trié à tab_cla
            for i in range (len(Lbis)):
                Lbis[i][0] = i+1
            self.tab_cla = Lbis
            
        
        if action == "Supprimer":
            #Objectif : Mettre à jour le classement quand un joueur quitte
            recherche = info
            trouver = False
            
            #Parcourt le tableau du classement, supprime le joueur recherché et met à jour les rangs
            for ligne in range(len(self.tab_cla)) :
                if trouver :
                    self.tab_cla[ligne-1][0] = self.tab_cla[ligne-1][0] - 1
        
                if not trouver and self.tab_cla[ligne][1] == recherche :
                    self.tab_cla.remove(self.tab_cla[ligne])
                    trouver = True
        
        s.SendToEveryone("classement", {"classement" :  tournoi.tab_cla})

    def affrontement(self, opposants):
        """Fonction qui attribut un plateau de jeu à 2 joueurs, et lance le match"""
        un_plateau_est_libre = False
        
        #Cherche si un plateau de jeu est libre
        for i in range(len(self.plateaux)):
            if self.plateaux[i][1] == "libre":
                un_plateau_est_libre = True
                num_plateau = i
                break
        
        #Si aucun plateau est libre, un nouveau plateau est créé
        if not un_plateau_est_libre :
            num_plateau = len(self.plateaux)
            nouv_plateau = JeuPipopipette(num_plateau)
            self.plateaux.append([nouv_plateau,"libre"])
        
        #Envoi au 2 joueurs les infos nécessaires, change les états des joueurs et du plateau
        s.SendToList("combat", opposants, {"combat" :  opposants})
        tournoi.maj_cla("Etat", (opposants[0], opposants[1], num_plateau))
        jeu = self.plateaux[num_plateau][0]
        jeu.affectation(opposants[0], opposants[1])
        s.SendToList("tableaux", opposants, {"tableaux" : [jeu.tableau_point,
                                                           jeu.tableau_ligne,
                                                           jeu.tableau_pipopipette]})
        s.SendToList("joueur", opposants, {"joueur" : jeu.liste_adversaires[jeu.joueur]})
        
                    
class JeuPipopipette():
    """Gère le système de jeu, règles du jeu, création des traits, création des carrés."""  
    
    def __init__(self, num):
        """Initialise la taille du plateau et son numéro"""
        self.nbr_colonne = JEU_LARGEUR
        self.nbr_ligne = JEU_HAUTEUR
        self.recommencer()
        self.plat = num
        
    def affectation(self, j1, j2):
        """Définit quels joueurs sont en train de jouer sur le plateau"""
        (self.j1, self.j2) = (j1, j2)
        self.liste_adversaires = [self.j1, self.j2]
          
    def recommencer(self):
        """Réinitialise les différents tableaux créés. Ces tableaux gèrent les etats de 
        tous les points, des carrés et des lignes.
        Réinitialise le nombre de carrés créés et initialise le joueur à 1 (de cette façon, 
        le joueur qui débutera le match sera celui qui a été défié)."""
        self.tableau_point = []
        self.tableau_carre = []
        self.tableau_ligne = []
        self.tableau_pipopipette = []
        self.selection = []
        self.joueur = 1
        self.nbr_carre_rouge = 0
        self.nbr_carre_bleu = 0
        self.fin_de_partie = False
        
        # Création des différents points avec pour état initial "Neutre".
        for i in range (self.nbr_colonne):
            ligne = []
            for j in range (self.nbr_ligne):
                    ligne.append('Neutre')
            self.tableau_point.append(ligne)
        
        # Création des différents carrés. Ils sont composés de quatre arêtes
        # avec pour état initial "0".
        for i in range (self.nbr_colonne-1):
            ligne=[]
            for j in range (self.nbr_ligne-1):
                ligne.append(0)
            self.tableau_carre.append(ligne)
    
    def changer_etat(self, action, i, j):
        """Permet de changer l'état d'un point (pour l'état sélectioné ou validé) et d'un carré 
        (en incrémentant l'état de 1). Si un carré a pour état "4" alors le carré est complet,
        on peut le dessiner.""" 
        etat = self.tableau_point[i][j]
        
        if action == 'selection':
            #Le joueur sélectionne ou désélectionne un point
            if etat == 'Neutre':
                etat = 'Sélectionné'
                self.selection.append((i,j))
            elif etat == 'Sélectionné':
                etat = 'Neutre'
                self.selection.pop()
            
        elif action == 'validation':
            #2 points sont validés
            etat = 'Neutre'
        
        elif action == 'carré' :
            #Une arête d'un carré est dessinée
            self.tableau_carre[i][j] += 1
            if self.tableau_carre[i][j] == 4:
                self.tableau_carre[i][j] = self.joueur
                self.creer_carre(i,j)
                return
                
        self.tableau_point[i][j] = etat
    
    def creer_trait(self, liste):
        """Ajout des coordonnées d'un trait dans le tableau lignes"""
        (COL,LIG) = (0,1)
        (x_base,y_base) = (CONVERSION.get("Pixel largeur"),CONVERSION.get("Pixel hauteur"))
        
        #Récupère les données des points et définit la position du trait associé
        (i_1,j_1) = (liste[0][COL],liste[0][LIG])
        (i_2,j_2) = (liste[1][COL],liste[1][LIG])
        i_min = min(i_1,i_2)
        j_min = min(j_1,j_2)
        if i_1 == i_2 :
            trait = [2*i_min, 2*j_min +1]
        else :
            trait = [2*i_min +1, 2*j_min]
        
        #Vérifie si le trait a déjà été dessiné
        for ligne in self.tableau_ligne :
            if ligne == trait :
                return None
        
        #En fonction de la position du trait, augmente le nombre d'arêtes 
        #dessinées aux carrés associés
        if i_1 == i_2 :
            if i_1 == 0  :
                self.changer_etat('carré', i_min, j_min)
            elif i_1 == len(self.tableau_carre) :
                self.changer_etat('carré', i_min-1, j_min)
            else : 
                self.changer_etat('carré', i_min-1, j_min)
                self.changer_etat('carré', i_min, j_min)
        else : 
            if j_1 == 0 :
                self.changer_etat('carré', i_min, j_min)
            elif j_1 == len(self.tableau_carre) :
                self.changer_etat('carré', i_min, j_min-1)
            else : 
                self.changer_etat('carré', i_min, j_min-1)
                self.changer_etat('carré', i_min, j_min)
            
        self.tableau_ligne.append(trait)
        return("Ok")
    
    def creer_carre(self, i, j): 
        """Cette fonction permet de créer des listes avec toutes les informations nécessaires 
        pour dessiner un carré. Cette fonction assure aussi la possibilité de rejouer quand un
        joueur complète un carré. Enfin, elle vérifie si la partie n'est pas terminée (tous les 
        carrés sont complétés)."""
        (col,lig)=(i,j)
        (x_base,y_base) = (CONVERSION.get("Pixel largeur"),CONVERSION.get("Pixel hauteur"))
        
        #Définit la valeur d'une moitié de case, pour ensuite pouvoir dessiner au centre d'une case
        DEMI_CARRE_X=(CAN_LARGEUR//self.nbr_colonne)/2
        DEMI_CARRE_Y=(CAN_HAUTEUR//self.nbr_ligne)/2
        
        #Définit les coordonnées du carré liées aux colonne et ligne reçues
        (x1,y1)=(x_base*col, y_base*lig)
        (x2,y2)=(x_base*(col+1), y_base*(lig+1))
        
        #Définit le nombre de carré total (dessiné ou non) présent sur le plateau
        nbr_carre_total = (self.nbr_colonne-1)*(self.nbr_ligne-1)
        
        if self.joueur == 0 :
            #Augmente le nombre de carrés possédés par le joueur "0" 
            #et définit un carré de la couleur associée
            self.nbr_carre_rouge += 1
            rectangle = [x1+DEMI_CARRE_X, y1+DEMI_CARRE_Y, 
                         x2+DEMI_CARRE_X, y2+DEMI_CARRE_Y, 'red']
        else : 
            #Augmente le nombre de carrés possédés par le joueur "1"
            #et définit un carré de la couleur associée
            self.nbr_carre_bleu += 1
            rectangle = [x1+DEMI_CARRE_X, y1+DEMI_CARRE_Y, 
                         x2+DEMI_CARRE_X, y2+DEMI_CARRE_Y, 'blue']
        
        self.tableau_pipopipette.append(rectangle)
        
        #Vérifie si tous les carrés sont dessinés
        if len(self.tableau_pipopipette) ==  nbr_carre_total :
            self.fin_de_partie = True
        
        #Informe qu'au moins un carré a été complété durant ce tour
        self.carre_complet = True

    def accessible(self,liste):
        """Vérifie si les points sélectionnés sont voisins."""   
        (COL,LIG) = (0,1)
        (x_base,y_base) = (CONVERSION.get("Pixel largeur"),CONVERSION.get("Pixel hauteur"))
        
        #Définit la distance entre 2 points voisins
        NORME = CAN_LARGEUR//JEU_LARGEUR
        norme = 0
        
        #Parcourt la liste de points donnée en entrée et ajoute la norme de la distance
        #entre chaque point dans une liste
        (x1,y1)=(x_base*liste[0][COL],y_base*liste[0][LIG])
        (x2,y2)=(x_base*liste[1][COL],y_base*liste[1][LIG])
        norme = sqrt(((x2-x1)**2)+((y2-y1)**2))
        
        #Si les points ne sont pas à la bonne distance, la sélection n'est pas valide
        if norme != NORME : 
            return None
        
        return (liste)
    
    def valider(self):
        """Quand 2 points sont sélectionnés, vérifie s'ils sont voisins, si un trait n'existe
        pas déjà entre eux puis, si la sélection est valide, crée un trait, 
        change les états correspondants, et change le joueur si nécessaire"""
        self.carre_complet = False
        
        #Vérifie si les points sont voisins, désélectionne le 2e point sélectionné s'ils ne le sont pas
        liste = self.accessible(self.selection)
        if liste is None:
            self.changer_etat("selection", self.selection[1][0], self.selection[1][1])
            return
        
        #Vérifie si un trait n'existe pas déjà, désélectionne le 2e point sélectionné
        #si un trait existe déjà, crée un trait sinon
        if self.creer_trait(liste) is None :
            self.changer_etat("selection", self.selection[1][0], self.selection[1][1])
            return
        
        #Désélectionne les 2 points choisis (le trait a été fait)
        for pt in liste:
            self.changer_etat('validation', pt[0], pt[1])   
        self.selection = []
                
        #Change le joueur qui doit jouer si aucun carré n'a été complété
        if not self.carre_complet :
            if self.joueur == 0 :
                self.joueur = 1
            else :
                self.joueur = 0
        
        #Termine la partie si tous les carrés sont complétés
        if self.fin_de_partie == True :
            self.terminer()
            return ("Stop")
        
    def terminer(self):
        """Vérifie qui a gagné le match, réinitialise le plateau de jeu,
        change les scores des joueurs et change les états des 2 joueurs et du plateau"""
        
        #Vérifie quel joueur a gagné
        if self.nbr_carre_rouge > self.nbr_carre_bleu :
            gagnant = self.liste_adversaires[0]
            perdant = self.liste_adversaires[1]
        elif self.nbr_carre_rouge < self.nbr_carre_bleu :
            gagnant = self.liste_adversaires[1]
            perdant = self.liste_adversaires[0]
            
        #Permet d'envoyer les différents tableaux aux clients pour voir l'aspect final du plateau
        s.SendToList("tableaux", self.liste_adversaires, 
                     {"tableaux" : [self.tableau_point, self.tableau_ligne, 
                                    self.tableau_pipopipette]})
        
        #Réinitialise le plateau, met à jour les états et les scores, envoie du gagnant aux joueurs
        self.recommencer()
        tournoi.maj_cla("Resultat", (gagnant, perdant))
        tournoi.maj_cla("Etat", (self.j1, self.j2, self.plat))
        s.SendToList("fin", self.liste_adversaires, {"fin" : gagnant})
    
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
        """Après avoir reçu les coordonnées d'un point, lui change son état. Si deux points
        sont sélectionnés, fait appel à la fonction valider()."""
        print(data)
        arret = None
        
        #Récupère le plateau de jeu associé au joueur qui vient de cliqué
        who = self.nickname
        for i in range(len(tournoi.plateaux)):
            if tournoi.plateaux[i][1] != "libre":
                pseudo_1 = tournoi.plateaux[i][0].liste_adversaires[0]
                pseudo_2 = tournoi.plateaux[i][0].liste_adversaires[1]
                if who == pseudo_1 or who == pseudo_2:
                    jeu = tournoi.plateaux[i][0]
        
        #Si le joueur qui a cliqué n'est pas celui qui doit jouer, rien ne se passe
        if who != jeu.liste_adversaires[jeu.joueur]:
            return
        
        #Si aucun point n'est sélectionné ou si le joueur reclique sur un point
        (i,j) = data["souris"]
        if len(jeu.selection) == 0 or (i,j) == jeu.selection[0]:
            jeu.changer_etat("selection", i, j)
        #Si un 2e point est sélectionné
        else :
            jeu.changer_etat("selection", i, j)
            arret = jeu.valider()
        
        #Envoie les infos nécessaires aux joueurs si la partie n'est pas finie
        if arret != "Stop":
            self._server.SendToList("tableaux", jeu.liste_adversaires,
                                    {"tableaux" : [jeu.tableau_point, jeu.tableau_ligne, 
                                                   jeu.tableau_pipopipette]})
            self._server.SendToList("joueur", jeu.liste_adversaires, 
                                    {"joueur" : jeu.liste_adversaires[jeu.joueur]}) 
    
    def Network_nickname(self, data):
        """Récupère le pseudo des joueurs et les met dans une liste (liste_joueurs)."""
        self.nickname = data["nickname"]
        self._server.liste_joueurs.append(self.nickname)
        self._server.PrintPlayers()
        
        #Ajoute le joueur à la fin du classement avec un score initial et lui envoie le classement
        tournoi.tab_cla.append([len(self._server.liste_joueurs),self.nickname, 1000,"libre"])
        s.SendToEveryone("classement",{"classement" :  tournoi.tab_cla})
        self.Send({"action" : "start"}) 
   
    def Network_duel(self, data):
        """Vérifie si les 2 joueurs peuvent s'affronter et lance un match si oui"""
        (placement_1,placement_2) = (None, None)
        
        #Récupère la position des joueurs dans le tableau et vérifie s'ils sont libres
        for i in range (len(tournoi.tab_cla)):
            if data["duel"][0] == tournoi.tab_cla[i][1] :
                placement_1 = i
                if tournoi.tab_cla[placement_1][3] != "libre":
                    return
            if data["duel"][1] == tournoi.tab_cla[i][1] :
                placement_2 = i
                if tournoi.tab_cla[placement_2][3] != "libre":
                    return
            
            #Vérifie si les 2 joueurs ont un score assez proche et lance le match si oui
            if placement_1 is not None and placement_2 is not None :
                ecart = abs(tournoi.tab_cla[placement_1][2] - tournoi.tab_cla[placement_2][2])
                if ecart < 300:
                    tournoi.affrontement(data["duel"])
                    break
                #elif 200 <= ecart < 300 :
                    
        
    def Network_abandon(self, data):
        """Termine le match de celui qui abandonne et met à jour les infos liées"""
        
        #Récupère le perdant (celui qui envoie la data) et le gagnant
        gagnant = data["abandon"][1]
        perdant = data["abandon"][0]
        jeu = None
        
        #Cherche le plateau sur lequel les joueurs étaient
        for i in range(len(tournoi.plateaux)):
            if tournoi.plateaux[i][1] != "libre":
                pseudo_1 = tournoi.plateaux[i][0].liste_adversaires[0]
                pseudo_2 = tournoi.plateaux[i][0].liste_adversaires[1]
                if gagnant == pseudo_1 or gagnant == pseudo_2:
                    jeu = tournoi.plateaux[i][0]
                    num_plateau = i
                    break
        
        #Réinitialise le plateau et change les scores et les états
        if jeu is not None:
            jeu.recommencer()
            tournoi.maj_cla("Resultat", (gagnant, perdant))
            tournoi.maj_cla("Etat", (jeu.j1, jeu.j2, jeu.plat))
            s.SendToList("fin", jeu.liste_adversaires, {"fin" : gagnant})
        
                                           
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
        """Quand une nouvelle personne se connecte au serveur, le tableau du classement lui est envoyé."""
        print("New Player connected")
        self.players[player] = True
        player.Send({"action" : "classement", "classement" : tournoi.tab_cla})

    def PrintPlayers(self):
        print("players' nicknames :", [p.nickname for p in self.players])
  
    def DelPlayer(self, player):
        """Si un joueur quitte, on le retire du tournoi"""
        print("Deleting Player " + player.nickname + " at "+str(player.addr))
        self.liste_joueurs.remove(player.nickname)
        tournoi.maj_cla("Supprimer", player.nickname)
        del self.players[player]
       
    def SendToOthers(self, data):
        """Fonction permettant d'envoyer la data à tous les joueurs sauf au jouer qui joue."""
        [p.Send({"action" : "tableau", "tableau" : data["tableau"]}) for p in self.players 
                                                                     if p.nickname != data["who"]]
    
    def SendToEveryone(self, nom, data):
        """Fonction permettant d'envoyer la data à tous les joueurs."""
        [p.Send({"action": nom, nom : data[nom]}) for p in self.players]
    
    def SendToList(self, nom, liste, data):
        """Fonction permettant d'envoyer la data à tous les joueurs dans la liste associée."""
        for p in self.players :
            for destinataire in liste :
                if p.nickname == destinataire :
                    p.Send({"action": nom, nom : data[nom]})
    
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
tournoi = Tournoi()
s.Launch()
