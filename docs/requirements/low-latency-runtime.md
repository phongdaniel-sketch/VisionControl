# Low-latency runtime requirements

Desktop Controller: camera and inference workers, each newest-only slot, sequence
IDs processed once. Input controller stays on Qt thread. Reject results older
than150ms since read or captured before resume; no result watchdog releases at
150ms. Workers never send input. Shutdown workers before resources reopen.
One Euro position filter + bounded30ms prediction for free movement only; disable
prediction on pinch/lock/drag-release/Pause/loss. Do not feed predictions back as
measurements. Cursor tick independent of inference. Debug OFF by default disables
landmarks/log printing and diagnostic recording entry until toggled ON; preview
still visible. Recording remains explicit. Preserve100ms drag start/release and
expose release delay in Settings; no user calibration changes.
