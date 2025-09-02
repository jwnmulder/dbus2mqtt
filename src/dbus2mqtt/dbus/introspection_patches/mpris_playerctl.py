import dbus_fast.introspection as dbus_introspection

# taken from https://github.com/altdesktop/playerctl/blob/b19a71cb9dba635df68d271bd2b3f6a99336a223/playerctl/playerctl-daemon.c#L578
mpris_introspection_playerctl = dbus_introspection.Node.parse("""\
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
      <arg type="x" name="Offset" direction="in"/>
    </method>
    <method name="SetPosition">
      <arg type="o" name="TrackId" direction="in"/>
      <arg type="x" name="Offset" direction="in"/>
    </method>
    <method name="OpenUri">
      <arg type="s" name="Uri" direction="in"/>
    </method>
    <signal name="Seeked">
      <arg type="x" name="Position" direction="out"/>
    </signal>
  </interface>

  <interface name="org.mpris.MediaPlayer2.TrackList">
    <property name="Tracks" type="ao" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="invalidates"/>
    </property>
    <property name="CanEditTracks" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <method name="GetTracksMetadata">
      <arg direction="in" name="TrackIds" type="ao"/>
      <arg direction="out" name="Metadata" type="aa{sv}"/>
    </method>
    <method name="AddTrack">
      <arg direction="in" name="Uri" type="s"/>
      <arg direction="in" name="AfterTrack" type="o"/>
      <arg direction="in" name="SetAsCurrent" type="b"/>
    </method>
    <method name="RemoveTrack">
      <arg direction="in" name="TrackId" type="o"/>
    </method>
    <method name="GoTo">
      <arg direction="in" name="TrackId" type="o"/>
    </method>
    <signal name="TrackListReplaced">
      <arg name="Tracks" type="ao"/>
      <arg name="CurrentTrack" type="o"/>
    </signal>
    <signal name="TrackAdded">
      <arg name="Metadata" type="a{sv}"/>
      <arg name="AfterTrack" type="o"/>
    </signal>
    <signal name="TrackRemoved">
      <arg name="TrackId" type="o"/>
    </signal>
    <signal name="TrackMetadataChanged">
      <arg name="TrackId" type="o"/>
      <arg name="Metadata" type="a{sv}"/>
    </signal>
  </interface>

  <interface name="org.mpris.MediaPlayer2.Playlists">
    <method name="ActivatePlaylist">
      <arg direction="in" name="PlaylistId" type="o"/>
    </method>
    <method name="GetPlaylists">
      <arg direction="in" name="Index" type="u"/>
      <arg direction="in" name="MaxCount" type="u"/>
      <arg direction="in" name="Order" type="s"/>
      <arg direction="in" name="ReverseOrder" type="b"/>
      <arg direction="out" name="Playlists" type="a(oss)"/>
    </method>
    <property name="PlaylistCount" type="u" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Orderings" type="as" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="ActivePlaylist" type="(b(oss))" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <signal name="PlaylistChanged">
      <arg name="Playlist" type="(oss)"/>
    </signal>
  </interface>
</node>
""")
