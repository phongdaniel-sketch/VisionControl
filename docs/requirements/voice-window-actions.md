# Voice window actions

Accept exact close-window and lock-computer phrases, not shutdown/sleep aliases.
Close only the captured foreground window; reject desktop/taskbar and changed
targets. Send WM_CLOSE, never terminate a process or dismiss save prompts.
Lock through Windows LockWorkStation. Pause/release gesture input before either
action. Preserve preview-only behavior and recognition threshold.

Plan: add allowlisted commands and adapter methods; test dispatch and rejection
with mocks, never lock the developer desktop during automated verification.
