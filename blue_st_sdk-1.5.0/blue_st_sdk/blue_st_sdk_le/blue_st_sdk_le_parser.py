import collections
import struct


class BlueSTSDKLEParser(object):

    _BLUESTSDKLEDataType = "BLUESTSDKLEData"

    _c_types_conversion_table = {
        "uint8": "B",
        "uint16": "H",
        "uint32": "I",
        "int8": "b",
        "int16": "h",
        "int32": "i",
        "float": "f",
        "string": "s",
    }

    def __init__(self, catalog_entry) -> None:
        self._format = self._build_format(catalog_entry.get("decoding_schema"))
        self._component_name = catalog_entry.get("component", None)
        self._data_fields = self._build_data_fields(
            catalog_entry.get("decoding_schema")
        )

    def parse(self, bytes):
        BLUESTSDKLEData = collections.namedtuple(
            self._BLUESTSDKLEDataType, self._data_fields
        )
        unpacked_data = struct.unpack(self._format, bytes)
        blueSTSDKData = BLUESTSDKLEData._make((self._component_name, *unpacked_data))
        return blueSTSDKData

    def _build_format(self, decoding_schema):
        # Data decoded as Little Endian; use ">" for Big Endian.
        format = "<"
        for entry in decoding_schema:
            entry_type = entry["type"]
            if entry_type != "string":
                format += self._c_types_conversion_table.get(entry_type)
            else:
                format += str(entry["length"]) + self._c_types_conversion_table.get(
                    entry_type
                )
        return format

    def _build_data_fields(self, decoding_schema):
        data_fields = ["component"]
        for entry in decoding_schema:
            data_fields.append(entry["telemetry"])
        return data_fields


class BlueSTSDKLEParserError(Exception):
    pass
