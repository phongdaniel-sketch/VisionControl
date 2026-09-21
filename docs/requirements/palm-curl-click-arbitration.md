# Palm curl-click arbitration

- Palm mode keeps the pointer moving from the palm center; an open thumb does not
  freeze the pointer by itself.
- With the thumb open, curling and re-extending index clicks left, middle clicks
  middle, and index plus middle together clicks right.
- Scroll, zoom, and volume pose recognition must preserve the extended-finger
  preparation used by curl clicks.
- Once a curl cycle starts, gesture-v1 arbitration yields to the mouse click
  controller until the cycle completes or times out.
- Active scrolling still owns its motion and cancels conflicting click input.
- The gesture guide must describe Palm behavior separately from Index fingertip.
