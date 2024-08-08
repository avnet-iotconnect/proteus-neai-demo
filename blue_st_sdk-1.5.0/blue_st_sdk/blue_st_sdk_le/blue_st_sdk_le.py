from blue_st_sdk.blue_st_sdk_le.blue_st_sdk_le_catalog import BlueSTSDKLECatalog
from blue_st_sdk.blue_st_sdk_le.blue_st_sdk_le_azure_telemetry_formatter import (
    BlueSTSDKLEAzureTelemetryFormatter,
)


class BlueSTSDKLE(object):
    def __init__(self, catalog_url=None):
        self._catalog = BlueSTSDKLECatalog(url=catalog_url)
        self._formatter = BlueSTSDKLEAzureTelemetryFormatter()

    def parse_message(self, device_id, fw_id, payload_id, bytes):
        parser = self._catalog.get_parser(device_id, fw_id, payload_id)
        return parser.parse(bytes)

    def format_message(self, blueSTSDKLEData):
        return self._formatter.format(blueSTSDKLEData)

    def parse_and_format_message(self, device_id, fw_id, payload_id, bytes):
        data = self.parse_message(device_id, fw_id, payload_id, bytes)
        formatted_message = self.format_message(data)
        return formatted_message
