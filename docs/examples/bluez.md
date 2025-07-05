# Bluez

This configuration file demonstrates how to use dbus2mqtt to bridge D-Bus events from BlueZ (the official Linux Bluetooth protocol stack) to MQTT topics. It subscribes to relevant D-Bus signals and properties for both the Bluetooth adapter (`hci0`) and all Bluetooth devices managed by BlueZ. The configuration defines flows that:

* Monitor property changes and object lifecycle events (added/removed) for the Bluetooth adapter and devices.
* Retrieve the current state of the adapter or device using the `GetAll` method from the `org.freedesktop.DBus.Properties` interface.
* Publish the retrieved state as JSON payloads to structured MQTT topics, enabling real-time monitoring and integration with home automation or IoT systems.

This setup allows MQTT clients to receive updates about Bluetooth adapter and device states, as well as notifications when devices are removed, making it easier to integrate Bluetooth events into broader automation workflows.

Configuration activities

* dbus2mqtt setup using the supplied [bluez.yaml](https://github.com/jwnmulder/dbus2mqtt/blob/main/docs/examples/bluez.yaml)

Execute the following command to run dbus2mqtt with the example configuration in this repository.

```bash
uv run dbus2mqtt --config docs/examples/bluez.yaml
```

## Commands

The following table lists commands, their descriptions, and an example JSON payload for invoking them via MQTT.

Dbus methods can be invoked by sendig the JSON payload to MQTT topic `dbus2mqtt/bluez/hci0/command`. Method calls will be done for all matching dbus objects.

| Interface            | Method<br />Property  | Description                          | Example MQTT JSON Payload                          |
|----------------------|-----------------------|--------------------------------------|-------------------------------------------------|
| `org.bluez.Adapter1` | `StartDiscovery`      | Starts bluetooth discovery           | `{ "method": "StartDiscovery" }`                |
| `org.bluez.Adapter1` | `StopDiscovery`       | Stops bluetooth discovery            | `{ "method": "StopDiscovery" }`                         |
| `org.bluez.Device1` | `Connect`              |                                      | `{ "method": "Connect", "path": "/org/bluez/hci0/dev_A1_A2_A3_A4_A5_A6" }`                |
| `org.bluez.Device1` | `Disconnect`           |                                      | `{ "method": "Disconnect", "path": "/org/bluez/hci0/dev_A1_A2_A3_A4_A5_A6" }`                         |
| `org.bluez.Device1` | `Pair`                 |                                      | `{ "method": "Pair", "path": "/org/bluez/hci0/dev_A1_A2_A3_A4_A5_A6" }`                |
| `org.bluez.Device1` | `CancelPairing`        |                                      | `{ "method": "CancelPairing", "path": "/org/bluez/hci0/dev_A1_A2_A3_A4_A5_A6" }`                         |


https://manpages.ubuntu.com/manpages/noble/man5/org.bluez.
