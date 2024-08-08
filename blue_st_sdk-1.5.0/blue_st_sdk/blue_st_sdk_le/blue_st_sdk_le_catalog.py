import json
import requests

from blue_st_sdk.blue_st_sdk_le.blue_st_sdk_le_parser import BlueSTSDKLEParser


class BlueSTSDKLECatalog(object):

    _catalog_url = (
        "https://raw.githubusercontent.com/SW-Platforms/appconfig/release/bluestsdkle/catalog.json"
    )

    def __init__(self, url=None):
        try:
            catalog_url = self._catalog_url if not url else url
            response = requests.get(catalog_url)
            response.raise_for_status()
            self._catalog = response.json()
        except Exception as e:
            raise BlueSTSDKLECatalogError(
                "Catalog {} not reachable.".format(catalog_url)
            )

    def get_parser(self, device_id, fw_id, payload_id):
        catalog_entry = self.get_entry(device_id, fw_id, payload_id)
        return BlueSTSDKLEParser(catalog_entry)

    def get_entry(self, device_id, fw_id, payload_id):
        for entry in self._catalog:
            if (
                int(entry.get("device_id"), 0) == device_id
                and int(entry.get("fw_id"), 0) == fw_id
                and int(entry.get("payload_id"), 0) == payload_id
            ):
                return entry

        raise BlueSTSDKLECatalogError(
            "unknown catalog entry for ({device_id},{fw_id},{payload_id})".format(
                device_id=device_id, fw_id=fw_id, payload_id=payload_id
            )
        )


class BlueSTSDKLECatalogError(Exception):
    pass
