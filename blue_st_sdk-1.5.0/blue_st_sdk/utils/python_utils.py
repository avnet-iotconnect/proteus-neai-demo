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


"""python_utils

The python_utils module defines utility functions related to the Python
language.
"""


# IMPORT

from functools import wraps
from threading import RLock
from datetime import datetime
from datetime import timezone


# UTILITY FUNCTIONS.

def lock_for_object(obj, locks={}):
    """To be used to gain exclusive access to a shared object from different
    threads."""
    return locks.setdefault(id(obj), RLock())

def lock(self):
    """To be used to gain exclusive access to a block of code from different
    threads."""
    return RLock()

def synchronized(call):
    """To be used to synchronize a method called on the same object from
    different threads."""
    assert call.__code__.co_varnames[0] in ['self', 'cls']
    @wraps(call)
    def inner(*args, **kwds):
        with lock_for_object(args[0]):
            return call(*args, **kwds)
    return inner

def synchronized_with_attr(lock_name):
    """To be used to synchronize a method called on the same object from
    different threads."""
    def decorator(method):
        def synced_method(self, *args, **kws):
            lock = getattr(self, lock_name)
            with lock:
                return method(self, *args, **kws)
        return synced_method
    return decorator

def get_class(class_name):
    """Get a class from the class name throuth the 'reflection' property."""
    parts = class_name.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m

def naive_to_utc_time(naive_dt):
    """Converting the naive timestamp to UTC format as per ISO 8601 format.
    E.g.: "2021-05-05T12:50:12.608Z"

    For Python 3.8.
    """
    # ISO 8601, UTC.
    utc_dt = naive_dt.astimezone(timezone.utc)
    # ISO 8601, UTC, in UTC format.
    utc_str = utc_dt.isoformat(timespec = 'milliseconds').replace('+00:00', 'Z')
    return utc_str

def naive_to_utc_time_(naive_dt):
    """Converting the naive timestamp to UTC format as per ISO 8601 format.
    E.g.: "2021-05-05T12:50:12.608Z"

    For Python 3.5 - Deprecated.
    """
    import pytz
    # Timezone.
    tz = pytz.timezone('Europe/Rome')
    # ISO 8601, UTC.
    utc_dt = tz.localize(naive_dt, is_dst=None).astimezone(pytz.utc)
    # ISO 8601, UTC, in UTC format.
    utc_str = list(str(utc_dt))
    utc_str[10] = 'T'
    utc_str = utc_str[:-8]
    utc_str[-1] = 'Z'
    return "".join(utc_str)

def get_utc_time():
    """Getting the timestamp in UTC format as per ISO 8601 format.
    """
    # Local time.
    naive_dt = datetime.now()
    # Convert to ISO 8601, UTC, in UTC format.
    return naive_to_utc_time(naive_dt)
