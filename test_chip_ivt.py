#!/usr/bin/env python3
"""
Unit tests for Chip-IVT module.

These tests validate basic functionality without requiring hardware.
"""

import unittest
from unittest.mock import Mock, patch
from chip_ivt import Rego1000, HeatpumpMonitor


class TestRego1000(unittest.TestCase):
    """Test Rego1000 class."""
    
    def test_initialization(self):
        """Test Rego1000 can be initialized."""
        rego = Rego1000(port='/dev/null', baudrate=19200)
        self.assertEqual(rego.port, '/dev/null')
        self.assertEqual(rego.baudrate, 19200)
        self.assertIsNone(rego.connection)
    
    def test_checksum_calculation(self):
        """Test checksum calculation."""
        rego = Rego1000()
        # XOR checksum: 0x81 ^ 0x00 ^ 0x02 ^ 0x09 = 0x8a
        checksum = rego._calculate_checksum(bytes([0x81, 0x00, 0x02, 0x09]))
        self.assertEqual(checksum, 0x8a)
    
    def test_temperature_conversion(self):
        """Test temperature value conversion."""
        rego = Rego1000()
        with patch.object(rego, '_read_register', return_value=235):
            # 235 / 10.0 = 23.5°C
            temp = rego.read_temperature(Rego1000.REG_RADIATOR_RETURN_TEMP)
            self.assertEqual(temp, 23.5)
    
    def test_temperature_conversion_none(self):
        """Test temperature conversion when read fails."""
        rego = Rego1000()
        with patch.object(rego, '_read_register', return_value=None):
            temp = rego.read_temperature(Rego1000.REG_RADIATOR_RETURN_TEMP)
            self.assertIsNone(temp)


class TestHeatpumpMonitor(unittest.TestCase):
    """Test HeatpumpMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rego = Mock(spec=Rego1000)
        self.monitor = HeatpumpMonitor(self.rego)
    
    def test_initialization(self):
        """Test HeatpumpMonitor can be initialized."""
        self.assertEqual(self.monitor.rego, self.rego)
    
    def test_read_all_temperatures(self):
        """Test reading all temperature sensors."""
        self.rego.read_temperature.return_value = 20.0
        temps = self.monitor.read_all_temperatures()
        
        # Should have 8 temperature readings
        self.assertEqual(len(temps), 8)
        self.assertIn('Radiator Return', temps)
        self.assertIn('Outdoor', temps)
        
        # All should be 20.0 based on our mock
        for temp in temps.values():
            self.assertEqual(temp, 20.0)
    
    def test_read_status(self):
        """Test reading system status."""
        self.rego.read_status.return_value = 1  # Compressor ON
        status = self.monitor.read_status()
        
        self.assertIn('Compressor', status)
        self.assertEqual(status['Compressor'], 'ON')
    
    def test_read_status_none(self):
        """Test status when read fails."""
        self.rego.read_status.return_value = None
        status = self.monitor.read_status()
        
        # Should show N/A when connection fails
        self.assertEqual(status['Compressor'], 'N/A')


class TestRegisterConstants(unittest.TestCase):
    """Test Rego1000 register address constants."""
    
    def test_register_addresses(self):
        """Test that register addresses are defined correctly."""
        self.assertEqual(Rego1000.REG_RADIATOR_RETURN_TEMP, 0x0209)
        self.assertEqual(Rego1000.REG_RADIATOR_FORWARD_TEMP, 0x020A)
        self.assertEqual(Rego1000.REG_HOT_WATER_TEMP, 0x020B)
        self.assertEqual(Rego1000.REG_OUTDOOR_TEMP, 0x020C)
        self.assertEqual(Rego1000.REG_COMPRESSOR_STATUS, 0x01FF)
        self.assertEqual(Rego1000.REG_ALARM, 0x0212)


if __name__ == '__main__':
    unittest.main()
