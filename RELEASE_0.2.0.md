# Fluidra Pool 0.2.0

Breaking cleanup release.

## Changes

- Rename the Home Assistant domain from `fluidra_z250iq` to `fluidra_pool`.
- Rename the custom component directory to `custom_components/fluidra_pool`.
- Add explicit device profiles for `Z250iQ` heat pumps and `Victoria Smart Connect VS` / `VS200` pumps.
- Add pump entities: power switch, auto mode switch, speed select, speed sensors and diagnostics.
- Keep heat pump entities scoped to heat pump profiles only.
- Keep REST polling conservative and WebSocket push enabled.

## Upgrade note

Because the domain changed, remove the old `fluidra_z250iq` integration entry from Home Assistant and add `Fluidra Pool` again.
