# Fluidra Pool Home Assistant Integration

Integration Home Assistant pour equipements piscine Fluidra connectes via le cloud Fluidra.

## Objectif

Ce depot garde une architecture volontairement lisible et prudente :

- domaine Home Assistant : `fluidra_pool`
- une seule entree d'integration par compte Fluidra
- decouverte de tous les appareils pris en charge du compte
- API cloud Fluidra uniquement
- mises a jour temps reel via WebSocket cloud
- polling REST lent en filet de securite
- profils d'appareils explicites pour eviter de melanger les composants entre PAC et pompe

## Appareils pris en charge

La version courante gere :

- pompe a chaleur `Z250iQ`
- pompe a vitesse variable `Victoria Smart Connect VS` / `VS200`

## Entites

Pour la `Z250iQ`, l'integration expose :

- un `climate` pour marche/arret, mode, consigne et temperature d'eau
- des `sensor` pour temperatures et metriques utiles
- des `binary_sensor` pour marche et alarme `No Flow`
- un capteur diagnostic `Raw components`

Pour la pompe `Victoria Smart Connect VS` / `VS200`, l'integration expose :

- un `switch` marche/arret
- un `switch` mode automatique
- un `select` de vitesse quand le composant de vitesse est disponible
- des `sensor` de vitesse et diagnostics
- un capteur diagnostic `Raw components`

## Polling et API

L'integration privilegie les push WebSocket et limite le polling REST a un intervalle configurable de 5 a 120 minutes, avec une valeur par defaut a 15 minutes.

Les ecritures n'enchainent plus de refresh immediat agressif. Une mise a jour locale optimiste est appliquee, puis un refresh differe permet de recuperer la valeur confirmee par le cloud.

## Cartographie retenue

Composants PAC confirmes :

- `13` : marche / arret
- `14` : mode demande
- `15` : consigne
- `19` : temperature eau
- `67` : temperature air
- `28` : `No Flow`
- `80` : mode effectif
- `81` / `82` : bornes min / max de consigne selon le mode

Composants pompe VS :

- `9` : marche / arret
- `10` : mode automatique
- `11` : niveau de vitesse
- `15` : vitesse en pourcentage
- `20` : programmation
- `21` : information reseau

## Structure

Le code de l'integration est dans `custom_components/fluidra_pool`.

## Remerciements

Merci au projet `foXaCe/Fluidra-pool`, qui a servi de reference pour comprendre la prise en charge des pompes Fluidra et comparer les composants exposes.

Depot de reference : `https://github.com/foXaCe/Fluidra-pool`
