# Brio USB connection inspection — 2026-09-05

Read-only Windows hub queries on the Logitech BRIO USB device (VID 046D, PID 085E):

- Parent: Intel xHCI USB Root Hub (USB 3.0), port 4.
- ACPI location: HS04.
- USB_NODE_CONNECTION_INFORMATION_EX Speed = 2: High-Speed (USB 2.0).
- USB_NODE_CONNECTION_INFORMATION_EX_V2 Flags = 2.
- DeviceIsSuperSpeedCapableOrHigher = true.
- DeviceIsOperatingAtSuperSpeedOrHigher = false.
- Vendor/product descriptor matches Brio, confirming correct port.

Conclusion: the current negotiated link is USB 2.0, despite a USB 3-capable
camera and root hub. This does not prove bandwidth saturation or establish it
as the sole cause of ~20 FPS. Cable, physical port or intervening connection
must be checked; USB topology alone cannot identify which physical component
caused fallback. 480 Mbps is the nominal USB 2 high-speed line rate, not available
video payload throughput.

The user screenshot shows HDR, Auto Focus, Auto Exposure, Low Light Compensation
and Auto White Balance enabled; anti-flicker is NTSC 60 Hz. Exposure/low-light
behavior is a candidate for FPS reduction, not a measured cause yet. Test Low
Light Compensation off first, separately test HDR off, keep sufficient light,
and avoid long manual exposures. Anti-flicker should match actual lighting/mains
frequency. Do not infer location from language or automatically force 50 Hz.

Next: connect with a verified USB 3 data cable to a known USB 3 port directly,
re-run the operating-speed query, then repeat the same camera-only benchmark.
Change settings one at a time to separate USB effects from exposure effects.
No driver, exposure, calibration or user profile was changed during inspection.

Raw result: build/brio-usb-link.json. Read-only probe: build/check_brio_usb.py.
References:
- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbioctl/ns-usbioctl-_usb_node_connection_information_ex_v2_flags
- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbspec/ne-usbspec-_usb_device_speed
- https://secure.logitech.com/en-gb/discover/a/optimize-webcam-settings
