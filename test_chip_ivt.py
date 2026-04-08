"""Tests for chip_ivt module."""

import unittest
from unittest.mock import MagicMock, patch

from chip_ivt import (
    ALARM_REGISTER,
    CMD_READ_STANDARD_REGISTER,
    COMPRESSOR_REGISTER,
    CONTROLLER_ADDRESS,
    TEMP_REGISTERS,
    HeatpumpMonitor,
    Rego1000,
    calculate_checksum,
)


class TestChecksum(unittest.TestCase):
    """Tests for XOR checksum calculation."""

    def test_checksum_single_byte(self):
        self.assertEqual(calculate_checksum([0x42]), 0x42)

    def test_checksum_all_zeros(self):
        self.assertEqual(calculate_checksum([0x00, 0x00, 0x00]), 0x00)

    def test_checksum_known_request(self):
        # Request to read register 0x0209 (GT1)
        payload = [CONTROLLER_ADDRESS, CMD_READ_STANDARD_REGISTER, 0x02, 0x09]
        checksum = calculate_checksum(payload)
        # 0x81 ^ 0x02 ^ 0x02 ^ 0x09 = 0x88
        self.assertEqual(checksum, 0x88)


class TestRego1000(unittest.TestCase):
    """Tests for the Rego1000 serial protocol handler."""

    @patch("chip_ivt.serial.Serial")
    def test_connect_opens_serial(self, mock_serial_class):
        mock_serial = MagicMock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial

        rego = Rego1000(port="/dev/ttyUSB0", baudrate=19200)
        rego.connect()

        mock_serial_class.assert_called_once_with(
            port="/dev/ttyUSB0",
            baudrate=19200,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=2.0,
        )
        self.assertTrue(rego.is_connected)

    @patch("chip_ivt.serial.Serial")
    def test_read_register_returns_value(self, mock_serial_class):
        mock_serial = MagicMock()
        mock_serial.is_open = True
        # Simulate response for value 215 (21.5 °C)
        # Response: [0x01, 0x02, 0x00, 0xD7, checksum]
        resp_data = bytes([0x01, 0x02, 0x00, 0xD7])
        checksum = calculate_checksum(resp_data)
        mock_serial.read.return_value = resp_data + bytes([checksum])
        mock_serial_class.return_value = mock_serial

        rego = Rego1000()
        rego.connect()
        value = rego.read_register(0x0209)

        self.assertEqual(value, 215)

    @patch("chip_ivt.serial.Serial")
    def test_read_register_negative_temperature(self, mock_serial_class):
        mock_serial = MagicMock()
        mock_serial.is_open = True
        # Simulate -50 (0xFFCE as unsigned 16-bit)
        resp_data = bytes([0x01, 0x02, 0xFF, 0xCE])
        checksum = calculate_checksum(resp_data)
        mock_serial.read.return_value = resp_data + bytes([checksum])
        mock_serial_class.return_value = mock_serial

        rego = Rego1000()
        rego.connect()
        value = rego.read_register(0x020C)

        self.assertEqual(value, -50)

    @patch("chip_ivt.serial.Serial")
    def test_read_register_checksum_mismatch(self, mock_serial_class):
        mock_serial = MagicMock()
        mock_serial.is_open = True
        # Response with bad checksum
        mock_serial.read.return_value = bytes([0x01, 0x02, 0x00, 0xD7, 0xFF])
        mock_serial_class.return_value = mock_serial

        rego = Rego1000()
        rego.connect()
        value = rego.read_register(0x0209)

        self.assertIsNone(value)

    def test_read_register_not_connected(self):
        rego = Rego1000()
        value = rego.read_register(0x0209)
        self.assertIsNone(value)

    @patch("chip_ivt.serial.Serial")
    def test_read_register_incomplete_response(self, mock_serial_class):
        mock_serial = MagicMock()
        mock_serial.is_open = True
        mock_serial.read.return_value = bytes([0x01, 0x02])  # Only 2 bytes
        mock_serial_class.return_value = mock_serial

        rego = Rego1000()
        rego.connect()
        value = rego.read_register(0x0209)

        self.assertIsNone(value)


class TestHeatpumpMonitor(unittest.TestCase):
    """Tests for the HeatpumpMonitor high-level API."""

    def test_read_temperature_converts_tenths(self):
        mock_rego = MagicMock()
        mock_rego.read_register.return_value = 215  # 21.5 °C
        monitor = HeatpumpMonitor(mock_rego)

        temp = monitor.read_temperature("GT1 Radiator Forward")

        self.assertAlmostEqual(temp, 21.5)
        mock_rego.read_register.assert_called_once_with(TEMP_REGISTERS["GT1 Radiator Forward"])

    def test_read_temperature_returns_none_on_failure(self):
        mock_rego = MagicMock()
        mock_rego.read_register.return_value = None
        monitor = HeatpumpMonitor(mock_rego)

        temp = monitor.read_temperature("GT1 Radiator Forward")

        self.assertIsNone(temp)

    def test_read_all_temperatures(self):
        mock_rego = MagicMock()
        mock_rego.read_register.return_value = 200  # 20.0 °C for all
        monitor = HeatpumpMonitor(mock_rego)

        temps = monitor.read_all_temperatures()

        self.assertEqual(len(temps), len(TEMP_REGISTERS))
        for temp in temps.values():
            self.assertAlmostEqual(temp, 20.0)

    def test_compressor_running(self):
        mock_rego = MagicMock()
        mock_rego.read_register.return_value = 1
        monitor = HeatpumpMonitor(mock_rego)

        self.assertTrue(monitor.read_compressor_status())
        mock_rego.read_register.assert_called_with(COMPRESSOR_REGISTER)

    def test_compressor_off(self):
        mock_rego = MagicMock()
        mock_rego.read_register.return_value = 0
        monitor = HeatpumpMonitor(mock_rego)

        self.assertFalse(monitor.read_compressor_status())

    def test_alarm_no_alarm(self):
        mock_rego = MagicMock()
        mock_rego.read_register.return_value = 0
        monitor = HeatpumpMonitor(mock_rego)

        self.assertEqual(monitor.read_alarm(), 0)
        mock_rego.read_register.assert_called_with(ALARM_REGISTER)


if __name__ == "__main__":
    unittest.main()
