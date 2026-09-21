# Implementation and acceptance

1. Add a deterministic contact latch shared by runtime and inert rehearsal.
2. Change curl mapping; prioritize contact in primary arbitration and mouse
   control while preserving active drag and existing release guarantees.
3. Update English/Vietnamese guide, calibration rehearsal and contact schematic.
4. Test immediate emission, no repeats, rearm, cold contact, ambiguous pinches,
   drag ownership, tracking loss, simulated arbitration, and updated curl mapping.
5. Run full tests and render the rehearsal. Physical acceptance still required:
   twenty thumb/middle touches must produce twenty right clicks on contact,
   held contact must not repeat, paired curls must produce only middle clicks,
   and left click/drag/scroll must remain usable.
