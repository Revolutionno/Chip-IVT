"""
Chip-IVT: Service tool for IVT heatpump Rego 1000 controller.

Communicates with IVT heatpumps via RS-232 serial using the Rego 1000 protocol.
Supports temperature monitoring, compressor status, and alarm checking.
"""

import argparse
import logging
import signal
import sys
import time

import serial

logger = logging.getLogger(__name__)

# Rego 1000 protocol constants
CONTROLLER_ADDRESS = 0x81
RESPONSE_ADDRESS = 0x01
CMD_READ_STANDARD_REGISTER = 0x02

# Temperature sensor registers (values stored as tenths of °C)
TEMP_REGISTERS = {
    "GT1 Radiator Forward": 0x0209,
    "GT2 Radiator Return": 0x020A,
    "GT3 Hot Water": 0x020B,
    "GT6 Outdoor": 0x020C,
    "GT8 Indoor": 0x020D,
    "GT9 Compressor": 0x020E,
    "GT10 Heat Carrier Forward": 0x020F,
    "GT11 Heat Carrier Return": 0x0210,
}

# Status registers
COMPRESSOR_REGISTER = 0x01FF
ALARM_REGISTER = 0x0212


def calculate_checksum(data):
    """Calculate XOR checksum for a sequence of bytes."""
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum


class Rego1000:
    """Serial protocol handler for Rego 1000 heatpump controllers.

    Communicates via RS-232 at 19200 baud, 8N1, using XOR checksum
    validation for all read operations.
    """

    def __init__(self, port="/dev/ttyUSB0", baudrate=19200, timeout=2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

    def connect(self):
        """Open the serial connection to the heatpump controller."""
        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
        )
        logger.info("Connected to %s at %d baud", self.port, self.baudrate)

    def disconnect(self):
        """Close the serial connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("Disconnected from %s", self.port)

    @property
    def is_connected(self):
        """Check if the serial connection is open."""
        return self._serial is not None and self._serial.is_open

    def read_register(self, register):
        """Read a 16-bit value from a Rego 1000 register.

        Args:
            register: Register address (e.g. 0x0209 for GT1).

        Returns:
            Integer register value, or None if the read fails.
        """
        if not self.is_connected:
            logger.error("Not connected to heatpump")
            return None

        reg_high = (register >> 8) & 0xFF
        reg_low = register & 0xFF
        payload = bytes([CONTROLLER_ADDRESS, CMD_READ_STANDARD_REGISTER, reg_high, reg_low])
        checksum = calculate_checksum(payload)
        request = payload + bytes([checksum])

        try:
            self._serial.reset_input_buffer()
            self._serial.write(request)
            response = self._serial.read(5)

            if len(response) != 5:
                logger.warning(
                    "Incomplete response for register 0x%04X: got %d bytes",
                    register,
                    len(response),
                )
                return None

            expected_checksum = calculate_checksum(response[:4])
            if response[4] != expected_checksum:
                logger.warning(
                    "Checksum mismatch for register 0x%04X: expected 0x%02X, got 0x%02X",
                    register,
                    expected_checksum,
                    response[4],
                )
                return None

            value = (response[2] << 8) | response[3]
            # Handle signed 16-bit values
            if value >= 0x8000:
                value -= 0x10000
            return value

        except serial.SerialException as exc:
            logger.error("Serial error reading register 0x%04X: %s", register, exc)
            return None


class HeatpumpMonitor:
    """High-level API for monitoring IVT heatpump temperature and status.

    Provides methods to read all temperature sensors, check compressor
    status and alarms, and display a formatted status overview.
    """

    def __init__(self, rego):
        """Initialize the monitor with a Rego1000 instance.

        Args:
            rego: A connected Rego1000 instance.
        """
        self.rego = rego

    def read_temperature(self, name):
        """Read a single temperature sensor.

        Args:
            name: Sensor name matching a key in TEMP_REGISTERS.

        Returns:
            Temperature in °C as a float, or None on failure.
        """
        register = TEMP_REGISTERS.get(name)
        if register is None:
            logger.error("Unknown sensor: %s", name)
            return None
        raw = self.rego.read_register(register)
        if raw is None:
            return None
        return raw / 10.0

    def read_all_temperatures(self):
        """Read all temperature sensors.

        Returns:
            Dict mapping sensor name to temperature in °C (or None).
        """
        temps = {}
        for name in TEMP_REGISTERS:
            temps[name] = self.read_temperature(name)
        return temps

    def read_compressor_status(self):
        """Read the compressor on/off status.

        Returns:
            True if compressor is running, False if off, None on failure.
        """
        value = self.rego.read_register(COMPRESSOR_REGISTER)
        if value is None:
            return None
        return value != 0

    def read_alarm(self):
        """Read the alarm register.

        Returns:
            Alarm code as integer, or None on failure.
            A value of 0 means no active alarm.
        """
        return self.rego.read_register(ALARM_REGISTER)

    def display_status(self):
        """Print a formatted status overview to stdout."""
        print("=" * 50)
        print("  IVT Heatpump Status (Rego 1000)")
        print("=" * 50)

        temps = self.read_all_temperatures()
        print("\nTemperature Sensors:")
        print("-" * 40)
        for name, temp in temps.items():
            if temp is not None:
                print(f"  {name:<30s} {temp:>6.1f} °C")
            else:
                print(f"  {name:<30s}    N/A")

        compressor = self.read_compressor_status()
        print("\nCompressor:")
        print("-" * 40)
        if compressor is not None:
            status_str = "RUNNING" if compressor else "OFF"
            print(f"  Status: {status_str}")
        else:
            print("  Status: N/A")

        alarm = self.read_alarm()
        print("\nAlarms:")
        print("-" * 40)
        if alarm is not None:
            if alarm == 0:
                print("  No active alarms")
            else:
                print(f"  Alarm code: {alarm}")
        else:
            print("  Alarm status: N/A")

        print("=" * 50)


def main():
    """CLI entry point for chip-ivt."""
    parser = argparse.ArgumentParser(
        description="Chip-IVT: Service tool for IVT heatpump Rego 1000"
    )
    parser.add_argument(
        "--port",
        default="/dev/ttyUSB0",
        help="Serial port (default: /dev/ttyUSB0)",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=19200,
        help="Baud rate (default: 19200)",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Continuous monitoring mode",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=10.0,
        help="Monitoring interval in seconds (default: 10)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    rego = Rego1000(port=args.port, baudrate=args.baudrate)

    running = True

    def handle_signal(signum, frame):
        nonlocal running
        running = False
        print("\nShutting down...")

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        rego.connect()
        monitor = HeatpumpMonitor(rego)

        if args.monitor:
            print(f"Monitoring every {args.interval}s  (Ctrl+C to stop)\n")
            while running:
                monitor.display_status()
                print()
                time.sleep(args.interval)
        else:
            monitor.display_status()
    except serial.SerialException as exc:
        print(f"Error: Could not connect to {args.port}: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        rego.disconnect()


if __name__ == "__main__":
    main()
