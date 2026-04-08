# Chip-IVT

Service tool for IVT heatpump Rego 1000 controller.

Communicates with IVT heatpumps via RS-232 serial using the Rego 1000 protocol at 19200 baud 8N1. Supports temperature monitoring, compressor status, and alarm checking.

## Features

- Active logging of each temperature sensor (GT1, GT2, GT3, GT6, GT8, GT9, GT10, GT11)
- Single-shot status display and continuous monitoring modes
- Compressor status and alarm monitoring
- CLI and Python API

## Installation

```bash
pip install pyserial
pip install -e .
```

## Usage

### Command Line

Single status check:

```bash
chip-ivt --port /dev/ttyUSB0
```

Continuous monitoring:

```bash
chip-ivt --port /dev/ttyUSB0 --monitor --interval 5
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | `/dev/ttyUSB0` | Serial port |
| `--baudrate` | `19200` | Baud rate |
| `--monitor` | off | Continuous monitoring mode |
| `--interval` | `10` | Monitoring interval in seconds |
| `--verbose` | off | Enable debug logging |

### Python API

```python
from chip_ivt import Rego1000, HeatpumpMonitor

rego = Rego1000(port='/dev/ttyUSB0', baudrate=19200)
rego.connect()

monitor = HeatpumpMonitor(rego)
temps = monitor.read_all_temperatures()
monitor.display_status()

rego.disconnect()
```

## Hardware Setup

Connect the heatpump's RS-232 port to your computer using a USB-to-serial adapter. The Rego 1000 controller uses the following serial settings:

- **Baud rate:** 19200
- **Data bits:** 8
- **Parity:** None
- **Stop bits:** 1

### Serial Port Permissions (Linux)

Add your user to the `dialout` group:

```bash
sudo usermod -aG dialout $USER
```

Log out and back in for the change to take effect.

## Register Addresses

### Temperature Sensors (values in tenths of °C)

| Sensor | Register | Description |
|--------|----------|-------------|
| GT1 | `0x0209` | Radiator forward |
| GT2 | `0x020A` | Radiator return |
| GT3 | `0x020B` | Hot water |
| GT6 | `0x020C` | Outdoor |
| GT8 | `0x020D` | Indoor |
| GT9 | `0x020E` | Compressor |
| GT10 | `0x020F` | Heat carrier forward |
| GT11 | `0x0210` | Heat carrier return |

### Status Registers

| Register | Description |
|----------|-------------|
| `0x01FF` | Compressor status (0 = off, non-zero = running) |
| `0x0212` | Alarm code (0 = no alarm) |

## Running Tests

```bash
pip install pytest
python -m pytest test_chip_ivt.py -v
```

## Troubleshooting

- **Permission denied on serial port:** Add your user to the `dialout` group (see above).
- **No response from heatpump:** Verify the RS-232 cable is properly connected and the serial port is correct. Try `--verbose` to see debug output.
- **Checksum errors:** Check the cable for loose connections or electromagnetic interference.

## License

GPL-3.0
