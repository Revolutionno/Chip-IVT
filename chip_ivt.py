#!/usr/bin/env python3
"""
Chip's Rego 1000 IVT Heatpump Service Tool

A service tool for monitoring and testing IVT heatpumps with Rego 1000 controllers.
This tool provides capabilities to read parameters, monitor status, and perform
diagnostics on Rego 1000-equipped heatpumps.
"""

import sys
import argparse
import serial
import time
from typing import Optional, Dict, Any


class Rego1000:
    """
    Communication handler for Rego 1000 controller.
    
    The Rego 1000 uses a serial protocol for communication.
    This class handles the low-level protocol communication.
    """
    
    # Rego 1000 command codes
    CMD_READ_REGISTER = 0x00
    CMD_WRITE_REGISTER = 0x01
    
    # Common register addresses
    REG_RADIATOR_RETURN_TEMP = 0x0209      # Radiator return temperature
    REG_RADIATOR_FORWARD_TEMP = 0x020A     # Radiator forward temperature
    REG_HOT_WATER_TEMP = 0x020B            # Hot water temperature
    REG_OUTDOOR_TEMP = 0x020C              # Outdoor temperature
    REG_INDOOR_TEMP = 0x020D               # Indoor temperature
    REG_COMPRESSOR_TEMP = 0x020E           # Compressor temperature
    REG_HEATCARRIER_RETURN = 0x020F        # Heat carrier return temperature
    REG_HEATCARRIER_FORWARD = 0x0210       # Heat carrier forward temperature
    REG_ALARM = 0x0212                     # Alarm status
    REG_COMPRESSOR_STATUS = 0x01FF         # Compressor on/off status
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 19200, timeout: int = 2):
        """
        Initialize connection to Rego 1000 controller.
        
        Args:
            port: Serial port device (e.g., /dev/ttyUSB0 or COM1)
            baudrate: Baud rate for serial communication (default 19200)
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection: Optional[serial.Serial] = None
    
    def connect(self) -> bool:
        """
        Establish connection to the Rego 1000 controller.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            print(f"Connected to Rego 1000 on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Close the serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Disconnected from Rego 1000")
    
    def _calculate_checksum(self, data: bytes) -> int:
        """
        Calculate checksum for Rego 1000 protocol.
        
        Args:
            data: Data bytes to calculate checksum for
            
        Returns:
            Checksum byte
        """
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum
    
    def _read_register(self, address: int) -> Optional[int]:
        """
        Read a register from the Rego 1000.
        
        Args:
            address: Register address to read
            
        Returns:
            Register value or None if read failed
        """
        if not self.connection or not self.connection.is_open:
            print("Not connected to Rego 1000")
            return None
        
        try:
            # Build command packet
            addr_high = (address >> 8) & 0xFF
            addr_low = address & 0xFF
            command = bytes([0x81, self.CMD_READ_REGISTER, addr_high, addr_low])
            checksum = self._calculate_checksum(command)
            packet = command + bytes([checksum])
            
            # Send command
            self.connection.write(packet)
            
            # Read response (expected: 5 bytes for successful read)
            response = self.connection.read(5)
            
            if len(response) == 5:
                # Verify checksum
                calc_checksum = self._calculate_checksum(response[:-1])
                if calc_checksum == response[-1]:
                    # Extract value (big-endian signed 16-bit)
                    value = (response[2] << 8) | response[3]
                    # Convert to signed
                    if value & 0x8000:
                        value = value - 0x10000
                    return value
                else:
                    print(f"Checksum error reading register 0x{address:04X}")
            else:
                print(f"Invalid response length: {len(response)} bytes")
            
            return None
            
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            return None
    
    def read_temperature(self, register: int) -> Optional[float]:
        """
        Read a temperature value from a register.
        
        Temperature values are stored as tenths of degrees Celsius.
        
        Args:
            register: Register address to read
            
        Returns:
            Temperature in degrees Celsius or None if read failed
        """
        value = self._read_register(register)
        if value is not None:
            return value / 10.0
        return None
    
    def read_status(self, register: int) -> Optional[int]:
        """
        Read a status value from a register.
        
        Args:
            register: Register address to read
            
        Returns:
            Status value or None if read failed
        """
        return self._read_register(register)


class HeatpumpMonitor:
    """Monitor and display heatpump status."""
    
    def __init__(self, rego: Rego1000):
        """
        Initialize heatpump monitor.
        
        Args:
            rego: Rego1000 instance for communication
        """
        self.rego = rego
    
    def read_all_temperatures(self) -> Dict[str, Optional[float]]:
        """
        Read all temperature sensors.
        
        Returns:
            Dictionary of sensor names to temperature values
        """
        temps = {
            'Radiator Return': self.rego.read_temperature(Rego1000.REG_RADIATOR_RETURN_TEMP),
            'Radiator Forward': self.rego.read_temperature(Rego1000.REG_RADIATOR_FORWARD_TEMP),
            'Hot Water': self.rego.read_temperature(Rego1000.REG_HOT_WATER_TEMP),
            'Outdoor': self.rego.read_temperature(Rego1000.REG_OUTDOOR_TEMP),
            'Indoor': self.rego.read_temperature(Rego1000.REG_INDOOR_TEMP),
            'Compressor': self.rego.read_temperature(Rego1000.REG_COMPRESSOR_TEMP),
            'Heat Carrier Return': self.rego.read_temperature(Rego1000.REG_HEATCARRIER_RETURN),
            'Heat Carrier Forward': self.rego.read_temperature(Rego1000.REG_HEATCARRIER_FORWARD),
        }
        return temps
    
    def read_status(self) -> Dict[str, Any]:
        """
        Read system status.
        
        Returns:
            Dictionary of status information
        """
        status = {
            'Compressor': 'ON' if self.rego.read_status(Rego1000.REG_COMPRESSOR_STATUS) else 'OFF',
            'Alarm': self.rego.read_status(Rego1000.REG_ALARM),
        }
        return status
    
    def display_status(self):
        """Display current heatpump status."""
        print("\n" + "="*60)
        print("Rego 1000 IVT Heatpump Status")
        print("="*60)
        
        print("\nTemperatures:")
        print("-" * 60)
        temps = self.read_all_temperatures()
        for name, temp in temps.items():
            if temp is not None:
                print(f"  {name:.<30} {temp:>6.1f} °C")
            else:
                print(f"  {name:.<30} {'N/A':>6}")
        
        print("\nSystem Status:")
        print("-" * 60)
        status = self.read_status()
        for name, value in status.items():
            print(f"  {name:.<30} {str(value):>6}")
        
        print("="*60)
    
    def monitor_continuous(self, interval: int = 5):
        """
        Continuously monitor and display status.
        
        Args:
            interval: Update interval in seconds
        """
        print(f"Monitoring heatpump (updating every {interval} seconds)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.display_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")


def main():
    """Main entry point for the service tool."""
    parser = argparse.ArgumentParser(
        description='Chip\'s Rego 1000 IVT Heatpump Service Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --port /dev/ttyUSB0 --monitor
  %(prog)s --port COM1 --status
  %(prog)s --port /dev/ttyUSB0 --monitor --interval 10
        """
    )
    
    parser.add_argument(
        '--port', '-p',
        default='/dev/ttyUSB0',
        help='Serial port device (default: /dev/ttyUSB0)'
    )
    
    parser.add_argument(
        '--baudrate', '-b',
        type=int,
        default=19200,
        help='Baud rate (default: 19200)'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Display current status once and exit'
    )
    
    parser.add_argument(
        '--monitor', '-m',
        action='store_true',
        help='Continuously monitor heatpump status'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=5,
        help='Update interval in seconds for monitoring mode (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Create Rego 1000 connection
    rego = Rego1000(port=args.port, baudrate=args.baudrate)
    
    if not rego.connect():
        print("Failed to connect to Rego 1000 controller")
        return 1
    
    try:
        monitor = HeatpumpMonitor(rego)
        
        if args.monitor:
            monitor.monitor_continuous(interval=args.interval)
        else:
            # Default to status display
            monitor.display_status()
    
    finally:
        rego.disconnect()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
