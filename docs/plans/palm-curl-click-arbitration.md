# Palm curl-click correction plan

1. Let the primary gesture arbiter record extended index/middle preparation while
   it reserves an open-thumb motion gesture.
2. Yield to the click controller for an in-progress curl/re-extension cycle.
3. Keep active scroll ownership and all existing emergency releases.
4. Correct the Palm gesture guide and add regression coverage for left, middle,
   and right clicks while scroll is enabled.
5. Run the deterministic suite, compileall, and diff validation. Validate physical
   hand ergonomics with a fresh diagnostic recording afterward.
