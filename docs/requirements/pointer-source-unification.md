# Palm and fingertip pointer sources

The Settings UI exposes only Palm (default) and Index fingertip. Both use the
same current gesture engine, shown under Gestures; no Gesture v1 menu/toggle.
Palm movement continues while the thumb is open; open thumb still enables curl
clicks. Fingertip keeps thumb locking. Palm scroll pose reserves movement while
being confirmed, then scrolls without moving the pointer. Drag stays relative to
palm with 100 ms confirmation/release. Zoom/volume reserve pointer movement.
Assigned OK with three remaining fingers extended wins before drag starts; an
active drag keeps ownership. Unassigned OK must not block pinch drag.
Calibrate using the selected source; store palm calibration separately and keep
the existing fingertip calibration. Legacy profile identifiers remain readable.
