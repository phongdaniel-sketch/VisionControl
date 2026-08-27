# Plan: Responsive controls and device defaults

Status: IMPLEMENTED

1. Change fresh/reset defaults for camera, monitor mapping, cursor response, and
   cursor deadzone.
2. Preserve primary-display identity during monitor discovery and place it at
   fixed index `0`.
3. Suspend the Controller frame timer for the complete Settings session and
   resume it paused after Settings closes.
4. Clarify cursor tuning controls and measured processing FPS in the UI.
5. Add deterministic coverage, run required verification, rebuild the macOS app,
   and perform a paused smoke check.
6. Replace fixed-display index entry with a named display combo matched to the
   runtime monitor order.
7. Add bundled high-contrast arrow assets and strengthen input/drop-down/spin
   button styling.

## Verification result

- Fresh/reset defaults are camera `1`, fixed primary display, cursor response
  `0.60`, and movement deadzone `0.5 px`.
- Monitor discovery deterministically moves the platform primary display to
  fixed index `0`; the current Mac reports its built-in Color LCD as primary.
- The Settings test confirms frame processing stops for the Settings session and
  resumes paused when it closes.
- The measured FPS label explicitly says `Processing`.
- The rebuilt packaged app remained alive during a paused Launch Services smoke
  check. Packaged Camera permission is still unavailable on the current Mac, so
  physical tracking awaits user authorization.
- Fixed display selection now exposes the Qt-provided names `Built-in Retina
  Display`, `DELL U2424HE`, and `ARZOPA`, with logical resolutions and a Primary
  marker while persisting the runtime monitor index.
- High-contrast SVG arrows are bundled into the app and used by combo and
  numeric controls; input surfaces, borders, button wells, hover, focus, and
  disabled states were visually checked in an offscreen Settings render.

## Safety

- Entering Settings releases all held input before frame processing stops.
- Exiting Settings never resumes active control automatically.
- Display and camera changes are applied only through validated local settings.
