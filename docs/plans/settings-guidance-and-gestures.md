# Plan: Settings guidance and configurable gestures

Status: IMPLEMENTED

1. Add reusable tooltip/accessibility descriptions to every Settings control,
   navigation destination, and footer action.
2. Move built-in gesture action/key editors into the Gestures cards and retain a
   locked fist safety card.
3. Repurpose Keyboard for arming/disarming timing controls.
4. Populate Advanced with implemented recognition, pinch, drag, and scroll
   thresholds plus validation.
5. Extend reset/save behavior and profile validation.
6. Add tests, visually inspect key pages, rebuild the app, and run it paused.

## Safety

- Fist remains reserved and cannot be assigned an action.
- Saving/reloading continues to pause and release all held input.
- Invalid advanced values are rejected before replacing the active profile.

## Verification result

- Gestures and Advanced pages were rendered offscreen at the target window size
  and remain readable without clipping.
- Gesture mapping plus keyboard-safety and Advanced values successfully
  round-trip through a validated local profile.
- Pinch start/release hysteresis is validated in both Settings and profile load.
- Tooltip/accessibility descriptions cover all Settings controls represented in
  deterministic tests.
- The rebuilt macOS app remains open in its safe paused/error state while the
  current packaged Camera permission is unavailable.
