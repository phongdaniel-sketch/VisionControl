# Settings guidance and configurable gestures

Status: APPROVED (user request on 2026-08-27)

## In-context guidance

- Every interactive Settings control must provide a concise tooltip explaining
  what it changes, the practical effect of higher/lower values where relevant,
  and any safety consequence.
- Sidebar destinations and footer actions must also explain their purpose.
- Tooltips must not replace visible labels or validation messages.

## Gesture configuration

- The Gestures page must allow editing each built-in configurable gesture:
  Disabled, Press, or Hold plus a supported key or multi-key chord.
- Keep fist visible but non-editable because it remains reserved for keyboard
  arming/disarming.
- Clearly state that users are configuring actions for built-in poses, not
  training new gesture shapes.
- Keep existing validated persistence and special-key support.

## Keyboard safety

- Use the Keyboard page for fist arming safety controls: hold time, release
  stability frames, cooldown, and automatic disarm after hand loss.
- Do not permit fist to be mapped to a keyboard action.

## Advanced page

- Expose only runtime parameters that are implemented and validated:
  recognition confidence, gesture activation frames, pinch close/open ratios,
  drag hold time, and scroll movement deadzone.
- Explain that defaults are recommended and invalid pinch hysteresis
  (`close >= open`) must be rejected.
- Camera frames and all settings remain local.

## Acceptance criteria

- Built-in gesture mappings can be edited and saved from the Gestures page.
- Keyboard safety and Advanced values round-trip through the existing profile.
- Reset restores all new controls from the default profile.
- All Settings controls have non-empty tooltips and deterministic tests pass.
