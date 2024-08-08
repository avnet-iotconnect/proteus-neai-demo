################################################################################
# COPYRIGHT(c) 2024 STMicroelectronics                                         #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided that the following conditions are met:  #
#   1. Redistributions of source code must retain the above copyright notice,  #
#      this list of conditions and the following disclaimer.                   #
#   2. Redistributions in binary form must reproduce the above copyright       #
#      notice, this list of conditions and the following disclaimer in the     #
#      documentation and/or other materials provided with the distribution.    #
#   3. Neither the name of STMicroelectronics nor the names of its             #
#      contributors may be used to endorse or promote products derived from    #
#      this software without specific prior written permission.                #
#                                                                              #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"  #
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE    #
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE   #
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE    #
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR          #
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF         #
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS     #
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN      #
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)      #
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE   #
# POSSIBILITY OF SUCH DAMAGE.                                                  #
################################################################################


"""virtualization_manager

The virtualization_manager module is responsible for managing the virtualization
of a device.
"""


# IMPORT

import logging
import os
import requests
#from abc import ABCMeta
#from abc import abstractmethod
#from concurrent.futures import ThreadPoolExecutor

from blue_st_sdk.utils.blue_st_exceptions import BlueSTInvalidOperationException
from blue_st_sdk.utils.python_utils import lock
from blue_st_sdk.utils.python_utils import lock_for_object
from blue_st_sdk.utils import fs_utils


# CLASSES

class VirtualizationManager(object):
    """Singleton class to manage the virtualization of the devices.
    """

    _INSTANCE = None
    """Instance object."""

    #_NUMBER_OF_THREADS = 5
    """Number of threads to be used to notify the listeners."""

    _VIRTUALIZATION_CATALOG_URL = "https://raw.githubusercontent.com/STMicroelectronics/appconfig/release/bluestsdkv2/catalog.json"
    """URL of the catalog of the virtualized devices."""

    _VIRTUALIZATION_CATALOG_PATH = "ble_catalog.json"
    """Filename of the catalog of the virtualized devices."""

    _GET_TIMEOUT_s = 10
    """Timeout in seconds for getting the catalog from the Internet."""

    def __init__(self):
        """Constructor.

        Raises:
            :exc:`Exception` is raised in case an instance of the same class has
            already been instantiated.
        """
        # Raise an exception if an instance has already been instantiated.
        if self._INSTANCE:
            msg = '\nAn instance of \'VirtualizationManager\' class already exists.'
            raise BlueSTInvalidOperationException(msg)

        #self._thread_pool = ThreadPoolExecutor(Manager._NUMBER_OF_THREADS)
        """Pool of thread used to notify the listeners."""

        #self._listeners = []
        """List of listeners to the manager changes.
        It is a thread safe list, so a listener can subscribe itself through a
        callback."""

        self._virtualization_catalog = None
        """Dictionary of the virtualized devices."""

    @classmethod
    def instance(self):
        """Getting an instance of the class.

        Returns:
            :class:`blue_st_sdk.virtualization.VirtualizationManager`: An
            instance of the class.
        """
        if self._INSTANCE is None:
            self._INSTANCE = VirtualizationManager()
        return self._INSTANCE

    def synchronize(self):
        """Pull the catalog of the virtualized devices from the Internet and
        store it to the filesystem; in case of issues with the connection use
        the local catalog if there, otherwise raise exception.

        Raises:
            :exc:`BlueSTInvalidOperationException` is raised in case the local
            device catalog is not found.
        """
        try:
            # Path to the local virtualization catalog.
            virtualization_catalog_path = os.path.join(
                os.path.expanduser('~'),
                self._VIRTUALIZATION_CATALOG_PATH)

            # Pulling the catalog of the virtualized devices from the Internet.
            logging.getLogger('BlueST').debug('Downloading device catalog from the Internet...: "{}"'.format(
                self._VIRTUALIZATION_CATALOG_URL))
            catalog = requests.get(
                self._VIRTUALIZATION_CATALOG_URL,
                timeout = self._GET_TIMEOUT_s)

            # Storing the virtualization catalog to the filesystem.
            logging.getLogger('BlueST').debug('Storing device catalog to the filesystem...: "{}"'.format(
                virtualization_catalog_path))
            self._virtualization_catalog = catalog.json()
            fs_utils.write_json_file(
                virtualization_catalog_path,
                self._virtualization_catalog)

        except Exception as e:
            if os.path.exists(virtualization_catalog_path):
                logging.getLogger('BlueST').debug('Using local device catalog: "{}".'.format(
                    virtualization_catalog_path))
                self._virtualization_catalog = fs_utils.read_json_file(virtualization_catalog_path)
            else:
                logging.getLogger('BlueST').debug('Local device catalog not found in: "{}".'.format(
                    virtualization_catalog_path))
                raise BlueSTInvalidOperationException('Local device catalog not found in: "{}".'.format(
                    virtualization_catalog_path))

    def get_device_entry(self, device_id, firmware_id=None):
        """Retrieve the device from the device catalog.

        Args:
            device_id (int): The device identifier.
            firmware_id (int): The firmware identifier (BlueST protocol v2 only).

        Returns:
            json: The entry of the device within the device catalog, if any,
            "None" otherwise. Refer to
            `json <https://docs.python.org/3/library/json.html>`_
            for more information.

        Raises:
            :exc:`BlueSTInvalidOperationException` is raised in case the local
            device catalog is not found.
        """
        try:
            # Synchronizing the virtualization catalog.
            if not self._virtualization_catalog:
                self.synchronize()

            # Searching for the given device in the virtualization catalog,
            # return it if found, else None.
            if self._virtualization_catalog:
                if not firmware_id:
                    for device in self._virtualization_catalog["bluestsdk_v1"]:
                        if int(device["ble_dev_id"], 16) == device_id:
                            return device
                else:
                    for device in self._virtualization_catalog["bluestsdk_v2"]:
                        if int(device["ble_dev_id"], 16) == device_id and \
                            int(device["ble_fw_id"], 16) == firmware_id:
                            return device
            return None

        except BlueSTInvalidOperationException as e:
            raise e

    def get_device_model(self, dtmi):
        """Retrieve the device model from the Internet.

        Args:
            dtmi (str): The Device Template Model Identifier.

        Returns:
            json: The device model of the device. Refer to
            `json <https://docs.python.org/3/library/json.html>`_
            for more information.
        """
        return None
