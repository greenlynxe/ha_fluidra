# Fluidra Pool 0.2.3

Correction des valeurs remontees par la pompe de filtration (Victoria Smart Connect VS).

## Contexte

Les composants utilises pour la pompe pointaient vers de mauvais identifiants :
l'id 11 est en fait le SKU, l'id 15 vaut toujours 0, et l'etat de vitesse etait
verrouille sur l'id 9 (toujours 0). Resultat : Home Assistant affichait une
vitesse a 0, un etat de marche errone et des capteurs diagnostic vides.

Les bons identifiants ont ete identifies en lisant l'API en direct (l'`uiconfig`
de la pompe renvoie une erreur 500 cote serveur et ne fournit aucun libelle).

## Changements

- **Vitesse de la pompe** : lue depuis la vraie consigne active (composant 17)
  au lieu d'un composant toujours nul. Le pourcentage affiche est enfin correct.
- **Etat de marche** : nouveau `binary_sensor` « Running » base sur le statut
  texte reel (`RUNNING`), avec le statut brut en attribut.
- **Interrupteur pompe** : son etat lu/affiche reflete desormais le vrai
  marche/arret (composant 13) au lieu d'un composant toujours a 0.
- **Nouveaux capteurs** : Statut, Mode de regulation (SPEED / FLOW),
  Fonction active, et Signal WiFi (dBm, diagnostic).
- **Capteurs diagnostic supprimes** : les anciens « Pump power value »,
  « Auto mode value », « Schedule value » et « Network value » remontaient des
  valeurs statiques ou nulles et ont ete retires.
- Les prereglages de vitesse (Low / Medium / High) correspondent maintenant aux
  consignes reellement rapportees par la pompe (50 / 75 / 80 %).

## Note

Le pilotage en ecriture de la pompe (interrupteur, selecteur de vitesse) n'a pas
ete modifie et reste a valider ; cette version corrige la lecture de l'etat.
