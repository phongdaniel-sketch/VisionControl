# Countdown display and paste phrases

Show a non-focusable countdown while a timer exists, including when the main
window is hidden. Update once per displayed second; hide on cancel, expiry and
shutdown. Keep recognition feedback separate. Timers remain session-only.
Accept exact longer Vietnamese paste phrases, never ambiguous 'da' or 'sao'.

Plan: add countdown label and exact aliases, test timer display lifecycle and
negative phrases, run regression/compile/diff checks. Real speech retest required.
