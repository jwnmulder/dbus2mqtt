# Bluez

Trying out this example

```bash
uv run dbus2mqtt --config docs/bluez.yaml
```

## TODOs

* InterfacesAdded and InterfacesRemoved signals work nicely for detecting new bluez devices.
  On startup however, we also want to publish state for existing bluez devices.

  Right now this is implemented with `interface_added` but this results in duplicate flows.
  We might want to do the same as BusNameOwnerChanged which dbus2mqtt translates in `bus_name_added` and `bus_name_removed`.
  Not all dbus objects however implement org.freedesktop.DBus.ObjectManager so this should be made configurable.

  Alternatively a trigger like `on_startup` would be more clear but that name alone does not indicate the flow is triggered for each interface.

* InterfacesAdded and InterfacesRemoved are triggered on org.bluez:/.
  These signals would ideally trigger flows subscribed on org.bluez:/org/bluez/hci0/dev_* to avoid duplication of flows.

  ```yaml
    actions:
      - type: publish_internal_event
        context:
          bus_name: org.bluez
          path: "{{ args[0]}}"
  ```

  ```yaml
    triggers:
      - type: internal_event
        filter: "{{ bus_name == 'org.bluez' and path.startswith('/org/bluez/hci0/dev_') }}"
    actions:
      - type: context_set
        context:
          device_properties: |
            {{ dbus_call('org.bluez', path, 'org.freedesktop.DBus.Properties', 'GetAll', ['org.bluez.Device1']) }}
  ```

  One concern is that the flow is triggered before the new interface is subscribed

* Make path optional and allow it to be set on interfaces. This way the flows can be combined as well. Unsure if this is makes sense though as we are now combining dbus objects of different kinds.

  This also means path wildcards need some more thought.

  bus_name = application
  path = object_path, an object within said application

  bus_name + path = dbus_fast proxy_object

### Multiple dbus objects

`BusNameSubscriptions` holds all dbus_fast proxy_objects for a given bus_name. This allows us to keep track of all objects that have to be cleared after the bus_name disappears from dbus. this works fine for mpris there each player instance has its own bus_name. It is less ideal for org.bluez which exists the entire time and it's the bluetooth devices that come and go, there we would want to cleanup based on objects disappearing from dbus.

For the first scenario, NameOwnerChanged works fine, for the second scenario NameOwnerChanged does not help much

TODOs

* Rename `BusNameSubscriptions` to `BusNameObjects` for clarity?
