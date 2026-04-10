# Fluidra Z250iQ Home Assistant Integration

Integration Home Assistant minimale et propre, dediee a la pompe a chaleur Fluidra `Z250iQ`.

## Objectif

Ce depot repart de zero avec un scope volontairement serre :

- un seul type d'appareil cible : `Z250iQ`
- API cloud Fluidra uniquement
- commandes confirmees : `power`, `mode`, `consigne`
- remontees temps reel via WebSocket cloud
- capteurs centres sur ce qu'on a valide en live

## Etat actuel

La version courante force aussi un refresh complet de securite toutes les 2 minutes, meme si le WebSocket est deja actif.

La premiere version expose :

- un `climate` pour piloter la PAC
- des `sensor` pour les temperatures et quelques metriques utiles
- des `binary_sensor` pour l'etat de marche et l'alarme `No Flow`
- un `config flow` avec auto-decouverte de la `Z250iQ` sur le compte Fluidra

## Cartographie retenue

Composants confirmes :

- `13` : marche / arret
- `14` : mode demande
- `15` : consigne
- `19` : temperature eau
- `67` : temperature air
- `28` : `No Flow`
- `80` : mode effectif
- `81` / `82` : bornes min / max de consigne selon le mode

Composants exposes comme diagnostics ou metriques estimees :

- `68` / `69` : temperatures eau entree / sortie
- `65` : temperature cote chaud
- `66` / `70` : temperatures cote froid
- `74` : tension alimentation
- `64` : puissance machine probable
- `77` : courant probable

## Structure

Le code de l'integration est dans `custom_components/fluidra_z250iq`.

## Remerciements

Merci au travail initial realise sur le projet `ha-fluidra-pool`, qui nous a servi de base de recherche et de point de depart technique pour cette integration centree sur la `Z250iQ`.

Mention speciale a son auteur, `@roagert`, pour le travail deja effectue autour de l'API Fluidra.

Depot d'origine : `https://github.com/Roagert/ha-fluidra-pool`
