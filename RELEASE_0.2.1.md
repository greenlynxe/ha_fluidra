# Fluidra Pool 0.2.1

Correctif de modele d'integration.

## Changements

- Une seule entree Home Assistant `Fluidra Pool` represente maintenant le compte Fluidra.
- Tous les appareils Fluidra pris en charge du compte sont decouverts au chargement.
- Chaque appareil conserve son propre coordinator, son WebSocket et son device Home Assistant.
- Le config flow ne demande plus de choisir un seul appareil.

## Note

Une entree creee avec la version `0.2.0` peut etre conservee: au prochain rechargement avec cette version, elle doit exposer tous les appareils pris en charge du compte.
