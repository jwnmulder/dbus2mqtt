import dbus_fast.introspection as dbus_introspection

# taken from https://code.videolan.org/videolan/vlc/-/blob/master/modules/control/dbus/dbus_introspect.h
mpris_introspection_vlc = dbus_introspection.Node.parse("""\
<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
  "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node>
  <interface name="org.freedesktop.DBus.Introspectable">
    <method name="Introspect">
      <arg name="data" direction="out" type="s"/>
    </method>
  </interface>

  <interface name="org.freedesktop.DBus.Properties">
    <method name="Get">
      <arg direction="in" type="s"/>
      <arg direction="in" type="s"/>
      <arg direction="out" type="v"/>
    </method>
    <method name="Set">
      <arg direction="in" type="s"/>
      <arg direction="in" type="s"/>
      <arg direction="in" type="v"/>
    </method>
    <method name="GetAll">
      <arg direction="in" type="s"/>
      <arg direction="out" type="a{sv}"/>
    </method>
    <signal name="PropertiesChanged">
      <arg type="s"/>
      <arg type="a{sv}"/>
      <arg type="as"/>
    </signal>
  </interface>

  <interface name="org.mpris.MediaPlayer2">
    <property name="CanQuit" type="b" access="read"/>
    <property name="Fullscreen" type="b" access="readwrite"/>
    <property name="CanSetFullscreen" type="b" access="read"/>
    <property name="CanRaise" type="b" access="read"/>
    <property name="HasTrackList" type="b" access="read"/>
    <property name="Identity" type="s" access="read"/>
    <property name="DesktopEntry" type="s" access="read"/>
    <property name="SupportedUriSchemes" type="as" access="read"/>
    <property name="SupportedMimeTypes" type="as" access="read"/>
    <method name="Raise"/>
    <method name="Quit"/>
  </interface>

  <interface name="org.mpris.MediaPlayer2.Player">
    <property name="PlaybackStatus" type="s" access="read"/>
    <property name="LoopStatus" type="s" access="readwrite"/>
    <property name="Rate" type="d" access="readwrite"/>
    <property name="Shuffle" type="b" access="readwrite"/>
    <property name="Metadata" type="a{sv}" access="read"/>
    <property name="Volume" type="d" access="readwrite"/>
    <property name="Position" type="x" access="read"/>
    <property name="MinimumRate" type="d" access="read"/>
    <property name="MaximumRate" type="d" access="read"/>
    <property name="CanGoNext" type="b" access="read"/>
    <property name="CanGoPrevious" type="b" access="read"/>
    <property name="CanPlay" type="b" access="read"/>
    <property name="CanPause" type="b" access="read"/>
    <property name="CanSeek" type="b" access="read"/>
    <property name="CanControl" type="b" access="read"/>
    <method name="Next"/>
    <method name="Previous"/>
    <method name="Pause"/>
    <method name="PlayPause"/>
    <method name="Stop"/>
    <method name="Play"/>
    <method name="Seek">
      <arg type="x" direction="in"/>
    </method>
    <method name="SetPosition">
      <arg type="o" direction="in"/>
      <arg type="x" direction="in"/>
    </method>
    <method name="OpenUri">
      <arg type="s" direction="in"/>
    </method>
    <signal name="Seeked">
      <arg type="x"/>
    </signal>
  </interface>

  <interface name="org.mpris.MediaPlayer2.TrackList">
    <property name="Tracks" type="ao" access="read"/>
    <property name="CanEditTracks" type="b" access="read"/>
    <method name="GetTracksMetadata">
      <arg type="ao" direction="in"/>
      <arg type="aa{sv}" direction="out"/>
    </method>
    <method name="AddTrack">
      <arg type="s" direction="in"/>
      <arg type="o" direction="in"/>
      <arg type="b" direction="in"/>
    </method>
    <method name="RemoveTrack">
      <arg type="o" direction="in"/>
    </method>
    <method name="GoTo">
      <arg type="o" direction="in"/>
    </method>
    <signal name="TrackListReplaced">
      <arg type="ao"/>
      <arg type="o"/>
    </signal>
    <signal name="TrackAdded">
      <arg type="a{sv}"/>
      <arg type="o"/>
    </signal>
    <signal name="TrackRemoved">
      <arg type="o"/>
    </signal>
    <signal name="TrackMetadataChanged">
      <arg type="o"/>
      <arg type="a{sv}"/>
    </signal>
  </interface>
</node>
""")
