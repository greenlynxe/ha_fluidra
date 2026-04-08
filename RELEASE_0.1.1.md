# 0.1.1

Premiere publication exploitable de l'integration `Fluidra Z250iQ` pour Home Assistant.

## Inclus dans cette version

- integration dediee a la PAC `Fluidra Z250iQ`
- authentification Fluidra via AWS Cognito
- recuperation des donnees via API cloud Fluidra
- mises a jour temps reel via WebSocket cloud
- entite `climate` pour le pilotage de la PAC
- capteurs principaux pour la temperature, l'etat et la telemetrie utile
- capteurs diagnostics supplementaires pour les composants internes identifies
- capteur d'`Efficience` base sur la puissance absorbee et le delta entree/sortie eau
- `config flow` Home Assistant pour la configuration depuis l'UI

## Compatibilite HACS

- ajout de `hacs.json`
- `manifest.json` complete avec les champs attendus par HACS
- version d'integration explicite `0.1.1`

## Remerciements

Cette integration repart de zero pour se concentrer sur la `Z250iQ`, mais elle s'appuie sur le travail initial realise sur `ha-fluidra-pool`.

Merci a `@roagert` pour le travail deja effectue autour de l'API Fluidra :
https://github.com/Roagert/ha-fluidra-pool
