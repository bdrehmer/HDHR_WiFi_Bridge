# HDHR_WiFi_Bridge
Use a Raspberry Pi to turn your HDHomeRun into a wireless device

1 - follow these instructions to turn your Raspberry Pi into a WiFi bridge: https://willhaley.com/blog/raspberry-pi-wifi-ethernet-bridge/

2 - use udpBroadcastMsgForwarder.py to forward device discovery (multi-cast UDP) messages to the HDHR so that other computers running the Kodi HDHomeRun add-on or HDHomeRun software can find the HDHR.  To run the script:
python3 udpBroadcastMsgForwarder.py
