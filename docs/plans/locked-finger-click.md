# Implementation plan

1. Revise deterministic curl-cycle recognizer for left/right/middle arbitration.
2. Integrate new thumb_lock pointer mode with relative-palm pinch drag and
   safety release. Expose mode and fixed mappings in Settings and guide.
3. Test all click cycles, rejected ambiguity, pinch startup/release, drag anchor,
   middle-button failure retry and profile serialization; run full checks.
4. Back up/select local profile mode and update Vietnamese guide. Physical user
   camera acceptance remains necessary; do not claim accuracy from synthetic tests.
