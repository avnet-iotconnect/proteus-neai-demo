from abc import ABC, abstractmethod


class BlueSTSDKLEMessageFormatter(ABC):
    @abstractmethod
    def format(self, blueSTSDKLEData):
        pass


class BlueSTSDKLEMessageFormatterError(Exception):
    pass
