from blue_st_sdk.blue_st_sdk_le.blue_st_sdk_le_message_formatter import (
    BlueSTSDKLEMessageFormatter,
    BlueSTSDKLEMessageFormatterError,
)
from blue_st_sdk.blue_st_sdk_le.blue_st_sdk_le_parser import BlueSTSDKLEParser


class BlueSTSDKLEAzureTelemetryFormatter(BlueSTSDKLEMessageFormatter):
    def __init__(self) -> None:
        pass

    def format(self, blueSTSDKLEData):
        if type(blueSTSDKLEData).__name__ != BlueSTSDKLEParser._BLUESTSDKLEDataType:
            raise BlueSTSDKLEMessageFormatterError(
                "invalid input datatype: {datatype}".format(
                    datatype=type(blueSTSDKLEData).__name__
                )
            )

        formatted_data = {}
        for name, value in blueSTSDKLEData._asdict().items():
            if name != "component":
                formatted_data[name] = value

        if blueSTSDKLEData.component:
            return {blueSTSDKLEData.component: formatted_data}
        else:
            return formatted_data
