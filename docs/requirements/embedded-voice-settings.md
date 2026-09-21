# Embedded Voice settings

Voice is a normal stacked Settings page after Mouse, using the shared navigation
button builder. Remove the standalone sidebar popup action. The main Save applies
edited voice settings; closing without Save discards edits. Unchanged voice fields
must not block unrelated Settings saves when the microphone is disconnected.

Use English control labels and an English command reference with Vietnamese spoken
examples. Speech recognition and spoken responses remain Vietnamese. Keep the
explicit Voice Debug tool separate; no audio capture on opening Settings.

Implementation: reuse the voice form for embedded and legacy standalone callers;
disconnect status callbacks on embedded widget destruction. Test creation, save,
cleanup, menu position and absence of a voice popup. Verified 412 tests, compileall,
diff check and a native Windows Settings screenshot at 1180x800. No EXE rebuild.
