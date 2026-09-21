# Weather voice command

Add the exact Vietnamese command "Thời tiết hôm nay thế nào". Fetch a one-day
forecast from Open-Meteo in a worker thread and reply in Vietnamese with location,
condition, current/apparent temperature, daily low/high, humidity, precipitation
probability and likely period, wind and notable UV/rain/wind conditions.

Voice settings expose an English "Automatically detect weather location" option
and a required fallback location, defaulting to "Đà Nẵng". Automatic mode uses
Windows Location only when enabled. Permission, device or location failures fall
back to Open-Meteo geocoding for the saved city. No IP geolocation, Gemini prompt,
API key, continuous tracking or background weather request is allowed. Coordinates
or the fallback city are sent to Open-Meteo only after the weather command.

Network, malformed response and lookup failures produce a short Vietnamese spoken
failure response. The forecast is informational and is not an official severe
weather warning. Unit tests mock all location and HTTP boundaries; physical Windows
location permission and live weather remain explicit acceptance tests.
