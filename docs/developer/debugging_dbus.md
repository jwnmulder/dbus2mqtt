# Debugging dbus

Useful snippets for checking what's going on on dbus

```bash
# monitor all dbus traffic
dbus-monitor

# show introspection data for dbus objects
busctl --user introspect org.freedesktop.DBus /org/freedesktop/DBus
```

Useful snippts for MPRIS debugging

```bash
playerctl -l

busctl --user introspect org.mpris.MediaPlayer2.vlc /org/mpris/MediaPlayer2

dbus-send --print-reply --session --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep mpris
```
