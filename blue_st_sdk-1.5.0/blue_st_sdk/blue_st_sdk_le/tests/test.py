import unittest

from blue_st_sdk import blue_st_sdk_le


class BlueSTSDKLETest(unittest.TestCase):
    def setUp(self):
        self._blueSTSDKLE = blue_st_sdk_le.BlueSTSDKLE()

        self.ENVIRONMENTAL_COMPONENT_NAME = "environmental"
        self.ENVIRONMENTAL_DATA_TEMPERATURE_KEY = "temperature"
        self.ENVIRONMENTAL_DATA_HUMIDITY_KEY = "humidity"
        self.ENVIRONMENTAL_DATA_PRESSURE_KEY = "pressure"

        self.A_STRING_TELEMETRY_KEY = "a_string_telemetry"
        self.AN_INT8_TELEMETRY_KEY = "an_int8_telemetry"

    def tearDown(self):
        pass

    def testParseFloats(self):
        data = self._blueSTSDKLE.parse_message(
            device_id=0x0C,
            fw_id=0xFE,
            payload_id=0x00,
            bytes=b"\x66\x66\xbe\x41\x00\x00\x20\x42\x66\x86\x79\x44",
        )

        self.assertEqual(data.component, self.ENVIRONMENTAL_COMPONENT_NAME)
        self.assertAlmostEqual(data.temperature, 23.8, places=1)
        self.assertAlmostEqual(data.humidity, 40, places=1)
        self.assertAlmostEqual(data.pressure, 998.1, places=1)

    def testParseStringAndInt(self):
        data = self._blueSTSDKLE.parse_message(
            device_id=0x0C,
            fw_id=0xFE,
            payload_id=0x01,
            bytes=b"\x68\x65\x6c\x6c\x6f\x00",
        )

        self.assertEqual(data.component, None)
        self.assertEqual(data.a_string_telemetry, b"hello")
        self.assertEqual(data.an_int8_telemetry, 0)

    def testFormatMessageWithComponent(self):
        data = self._blueSTSDKLE.parse_message(
            device_id=0x0C,
            fw_id=0xFE,
            payload_id=0x00,
            bytes=b"\x66\x66\xbe\x41\x00\x00\x20\x42\x66\x86\x79\x44",
        )
        formatted_message = self._blueSTSDKLE.format_message(data)

        self.assertIsInstance(formatted_message, dict)
        self.assertIn(self.ENVIRONMENTAL_COMPONENT_NAME, formatted_message)
        self.assertIn(
            self.ENVIRONMENTAL_DATA_TEMPERATURE_KEY,
            formatted_message[self.ENVIRONMENTAL_COMPONENT_NAME],
        )
        self.assertIn(
            self.ENVIRONMENTAL_DATA_HUMIDITY_KEY,
            formatted_message[self.ENVIRONMENTAL_COMPONENT_NAME],
        )
        self.assertIn(
            self.ENVIRONMENTAL_DATA_PRESSURE_KEY,
            formatted_message[self.ENVIRONMENTAL_COMPONENT_NAME],
        )

        self.assertAlmostEqual(
            formatted_message[self.ENVIRONMENTAL_COMPONENT_NAME][
                self.ENVIRONMENTAL_DATA_TEMPERATURE_KEY
            ],
            23.8,
            places=1,
        )
        self.assertAlmostEqual(
            formatted_message[self.ENVIRONMENTAL_COMPONENT_NAME][
                self.ENVIRONMENTAL_DATA_HUMIDITY_KEY
            ],
            40,
            places=1,
        )
        self.assertAlmostEqual(
            formatted_message[self.ENVIRONMENTAL_COMPONENT_NAME][
                self.ENVIRONMENTAL_DATA_PRESSURE_KEY
            ],
            998.1,
            places=1,
        )

    def testFormatMessageWithoutComponent(self):
        data = self._blueSTSDKLE.parse_message(
            device_id=0x0C,
            fw_id=0xFE,
            payload_id=0x01,
            bytes=b"\x68\x65\x6c\x6c\x6f\x00",
        )
        formatted_message = self._blueSTSDKLE.format_message(data)

        self.assertIsInstance(formatted_message, dict)
        self.assertIn(self.A_STRING_TELEMETRY_KEY, formatted_message)
        self.assertIn(self.AN_INT8_TELEMETRY_KEY, formatted_message)

        self.assertEqual(formatted_message[self.A_STRING_TELEMETRY_KEY], b"hello")
        self.assertEqual(formatted_message[self.AN_INT8_TELEMETRY_KEY], 0)
