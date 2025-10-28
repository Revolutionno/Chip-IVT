#!/usr/bin/env python3
"""
Example script demonstrating programmatic use of the Chip-IVT library.

This example shows how to use the Rego1000 and HeatpumpMonitor classes
in your own Python scripts.
"""

from chip_ivt import Rego1000, HeatpumpMonitor


def main():
    """Demonstrate library usage."""
    # Create a Rego 1000 connection
    # Adjust the port to match your system
    rego = Rego1000(port='/dev/ttyUSB0', baudrate=19200)
    
    # Try to connect
    if not rego.connect():
        print("Failed to connect to Rego 1000")
        print("This is normal if you don't have a physical device connected.")
        print("\nTo use this tool with a real device:")
        print("1. Connect your USB-to-serial adapter")
        print("2. Update the port parameter above (e.g., /dev/ttyUSB0 or COM1)")
        print("3. Ensure the Rego 1000 is powered and connected")
        return
    
    try:
        # Create a monitor instance
        monitor = HeatpumpMonitor(rego)
        
        # Read and display all temperatures
        print("\nReading temperatures...")
        temps = monitor.read_all_temperatures()
        for sensor, temp in temps.items():
            if temp is not None:
                print(f"{sensor}: {temp:.1f}°C")
            else:
                print(f"{sensor}: N/A")
        
        # Read system status
        print("\nReading system status...")
        status = monitor.read_status()
        for name, value in status.items():
            print(f"{name}: {value}")
        
        # Display formatted status
        print("\nFormatted status display:")
        monitor.display_status()
        
    finally:
        # Always disconnect when done
        rego.disconnect()


if __name__ == '__main__':
    main()
