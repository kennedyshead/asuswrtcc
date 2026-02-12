# AsusWRTCC

An ASUSWRT router integration for Home Assistant that provides device tracking and sensor monitoring capabilities.

## Features

- **Device Tracking**: Monitor connected devices on your ASUSWRT router
- **Network Sensors**: Real-time network statistics including bandwidth usage
- **System Monitoring**: CPU usage, memory usage, temperature sensors, and uptime
- **Flexible Connection Methods**: Supports both SSH and Telnet protocols
- **Multiple Router Modes**: Works with both Access Point and Router configurations

## Supported Platforms

- Device Tracker
- Sensor

## Installation

### HACS (Recommended)

1. Add this repository to HACS
2. Search for "AsusWRTCC" in the HACS store
3. Install the integration

### Manual Installation

1. Copy the `custom_components/asuswrtcc` directory to your Home Assistant `custom_components` folder
2. Restart Home Assistant

## Configuration

### Configuration Options

- `interface`: Network interface to monitor (default: `eth0`)
- `dnsmasq`: Path to dnsmasq lease file (default: `/var/lib/misc`)
- `require_ip`: Require IP address for device tracking
- `ssh_key`: Path to SSH private key for authentication
- `track_unknown`: Track unknown devices

### Setup

1. Go to Home Assistant Configuration → Integrations
2. Click "Add Integration"
3. Search for "AsusWRTCC"
4. Enter your router's connection details
5. Configure the desired options

## Requirements

- Home Assistant 2025.12.0 or later
- `aioasuswrt==2.2.0`

## Connection Methods

### SSH

Use SSH for secure connection to your ASUSWRT router.

### Telnet

Use Telnet for connection (less secure than SSH).

## Sensors Available

- **Network**: RX/TX bytes and rates
- **System**: CPU usage (all cores), memory usage, load averages
- **Temperature**: 2.4GHz, 5.0GHz, and CPU temperatures
- **Status**: Uptime and last boot time
- **Devices**: Connected device count

## Router Modes

### Router Mode

For traditional router configurations.

### Access Point Mode

For access point configurations.

## Troubleshooting

- Ensure your router supports the required protocols
- Check firewall settings if connection fails
- Verify correct interface and dnsmasq paths
- Review Home Assistant logs for detailed error messages

## License

MIT License - Copyright 2025 Magnus Knutas