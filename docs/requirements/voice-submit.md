# Voice button submits on second activation

User correction: Voice click starts one capture; a second click stops capture and
submits it, not cancels. Apply the same semantics to Voice Listen Toggle gestures.
Automatic silence submission and 5/15-second safety deadlines remain unchanged.
Escape cancels capture or in-flight recognition. While processing, further clicks
do nothing. Preserve generation and cancellation token on submit; invalidate on
cancel. Hold hotkey and preview hold button retain release-to-submit semantics.

Plan: add explicit submit transition, ignore late listening progress after submit,
update button label/tooltip and busy states, test submit -> recognition -> execution,
test repeated clicks, early release, Escape cancellation and unchanged automatic mode.
Source-only; no real microphone or API use in automated tests.
