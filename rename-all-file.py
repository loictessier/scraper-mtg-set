import os

dossier = './output'

for nom_fichier in os.listdir(dossier):

    chemin_complet = os.path.join(dossier, nom_fichier)
    
    if os.path.isfile(chemin_complet):
        nouveau_nom = nom_fichier + ".jpg"
        chemin_nouveau_fichier = os.path.join(dossier, nouveau_nom)
        os.rename(chemin_complet, chemin_nouveau_fichier)

print("Renommage terminé.")