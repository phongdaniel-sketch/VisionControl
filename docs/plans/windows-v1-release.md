# Windows v1.0 release plan

1. Preserve the runtime pause state for Copy, Paste, and Close Window; retain mandatory
   pause for Lock Computer.
2. Add deterministic regression coverage for both initially active and paused states.
3. Set package, macOS bundle, and Windows executable metadata to 1.0.0.
4. Refresh README and Windows release documentation.
5. Run the full automated verification suite.
6. Build the Windows one-directory bundle, optionally Authenticode-sign it when a trusted
   certificate is present, and create a ZIP plus SHA-256 sidecar.
7. Commit, push, tag `v1.0.0`, and publish the two release assets on GitHub.

The release remains unsigned when no trusted code-signing certificate is installed. The
release notes must state that limitation; creating a self-signed certificate is not an
acceptable substitute for publisher identity or SmartScreen reputation.
