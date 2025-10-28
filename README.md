# Chip-IVT

Chip's Rego 1000 IVT heatpump service tool for monitoring and testing your heatpump.

## Overview

This service tool provides monitoring and diagnostic capabilities for IVT heatpumps equipped with Rego 1000 controllers. It communicates with the controller via serial connection to read temperatures, system status, and perform diagnostics.

## Features

- **Real-time Monitoring**: Continuously monitor all temperature sensors
- **System Status**: Check compressor status and alarm conditions
- **Serial Communication**: Direct communication with Rego 1000 controller
- **Command Line Interface**: Easy-to-use CLI for quick diagnostics
- **Extensible**: Built with a modular design for easy extension

## Monitored Parameters

The tool can monitor the following parameters:

- Radiator return and forward temperatures
- Hot water temperature
- Outdoor temperature
- Indoor temperature
- Compressor temperature
- Heat carrier return and forward temperatures
- Compressor status (ON/OFF)
- Alarm status

## Installation

### Prerequisites

- Python 3.6 or higher
- Serial port access (USB-to-serial adapter or built-in serial port)
- Rego 1000 controller with serial interface

### Install from source

```bash
git clone https://github.com/Revolutionno/Chip-IVT.git
cd Chip-IVT
pip install -r requirements.txt
python setup.py install
```

Or install in development mode:

```bash
pip install -e .
```

## Usage

### Basic Status Check

Display the current heatpump status once:

```bash
chip-ivt --port /dev/ttyUSB0 --status
```

Or simply (status is the default):

```bash
chip-ivt --port /dev/ttyUSB0
```

### Continuous Monitoring

Monitor the heatpump continuously with updates every 5 seconds:

```bash
chip-ivt --port /dev/ttyUSB0 --monitor
```

Monitor with a custom update interval (e.g., 10 seconds):

```bash
chip-ivt --port /dev/ttyUSB0 --monitor --interval 10
```

### Windows

On Windows, use COM port naming:

```bash
chip-ivt --port COM1 --monitor
```

### Command Line Options

```
usage: chip-ivt [-h] [--port PORT] [--baudrate BAUDRATE] [--status] [--monitor] [--interval INTERVAL]

Chip's Rego 1000 IVT Heatpump Service Tool

optional arguments:
  -h, --help            show this help message and exit
  --port PORT, -p PORT  Serial port device (default: /dev/ttyUSB0)
  --baudrate BAUDRATE, -b BAUDRATE
                        Baud rate (default: 19200)
  --status, -s          Display current status once and exit
  --monitor, -m         Continuously monitor heatpump status
  --interval INTERVAL, -i INTERVAL
                        Update interval in seconds for monitoring mode (default: 5)
```

## Hardware Setup

1. Connect a USB-to-serial adapter to your computer
2. Connect the adapter to the Rego 1000 controller's serial port
3. The Rego 1000 typically uses RS-232 communication at 19200 baud, 8N1
4. Ensure proper grounding and wiring according to Rego 1000 documentation

## Troubleshooting

### Cannot connect to serial port

- Check that the serial port exists: `ls /dev/ttyUSB*` (Linux) or check Device Manager (Windows)
- Ensure you have permissions: `sudo usermod -a -G dialout $USER` (Linux, then log out and back in)
- Verify the correct port name is used

### No data received

- Check physical connections to the Rego 1000
- Verify the baud rate (default 19200)
- Ensure the Rego 1000 serial interface is enabled

### Permission denied

On Linux, you may need to add your user to the dialout group:

```bash
sudo usermod -a -G dialout $USER
```

Then log out and log back in.

## Technical Details

### Communication Protocol

The Rego 1000 uses a proprietary serial protocol:

- Baud rate: 19200 bps
- Data bits: 8
- Parity: None
- Stop bits: 1
- Protocol: Custom packet-based with checksum validation

### Register Addresses

Common register addresses used by the tool:

- `0x0209`: Radiator return temperature
- `0x020A`: Radiator forward temperature
- `0x020B`: Hot water temperature
- `0x020C`: Outdoor temperature
- `0x020D`: Indoor temperature
- `0x020E`: Compressor temperature
- `0x020F`: Heat carrier return temperature
- `0x0210`: Heat carrier forward temperature
- `0x01FF`: Compressor status
- `0x0212`: Alarm status

Temperatures are stored as signed 16-bit integers representing tenths of degrees Celsius.

## Development

### Running directly

You can run the tool directly without installation:

```bash
python chip_ivt.py --port /dev/ttyUSB0 --monitor
```

### Code Structure

- `Rego1000`: Low-level serial communication class
- `HeatpumpMonitor`: High-level monitoring and display class
- `main()`: Command-line interface and argument parsing

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This is an unofficial tool and is not affiliated with or endorsed by IVT or the Rego 1000 manufacturer. Use at your own risk. Always refer to official documentation for your heatpump system.
