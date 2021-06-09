import csv
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

import requests
from netaddr import IPAddress

IP_TO_LOC = []  # type: List[IpRange]

# To update the dataset update the lates release with new dataset and then set
# this url.
IP_DATA_URL = "https://github.com/cultivateai/django-rest-authemail/releases/download/v2.1.3/ip_to_loc.csv"  # noqa
DATA_SAVE_PATH = "/usr/share/authemail"
DATA_FILE_NAME = "ip_to_loc.csv"
_PATH_JOINED = os.path.join(DATA_SAVE_PATH, DATA_FILE_NAME)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IpRange:
    """Wrapper for the loaded ip to location data."""

    start: int
    end: int
    country_code: str = "Unknown"
    country: str = "Unknown"
    region: str = "Unknown"
    city: str = "Unknown"


NOT_FOUND_RANGE = IpRange(start=-1, end=-1)


def download_ip_dataset():
    Path(DATA_SAVE_PATH).mkdir(parents=True, exist_ok=True)
    response = requests.get(IP_DATA_URL)
    with open(_PATH_JOINED, "wb") as f:
        f.write(response.content)


def _build_data() -> None:
    # We have already loaded the data no need to do it.
    if IP_TO_LOC:
        return

    # Data has not been downloaded yet
    if not os.path.isfile(_PATH_JOINED):
        logger.info("Downloading IP to location dataset...")
        download_ip_dataset()

    # File data is already sorted on start-end range and should not be
    # overlapping in any way
    with open(_PATH_JOINED) as data:
        csv_reader = csv.reader(data)

        for row in csv_reader:
            try:
                entry = IpRange(
                    start=int(row[0]),
                    end=int(row[1]),
                    country_code=row[2],
                    country=row[3],
                    region=row[4],
                    city=row[5],
                )
                IP_TO_LOC.append(entry)
            except IndexError:
                pass


def ip_str_to_int(ip_addr: str) -> int:
    """Convert an IP address string to an integer."""
    return IPAddress(ip_addr).value


def search_ip_ranges(ip_address: Union[str, int]) -> IpRange:
    """
    Search all the IP ranges for the passed in IP and return the matched data.

    Performing this search is a O(log n) operation where `n` is the number of
    ip ranges that exist in the dataset (i.e len(IP_TO_LOC)).

    Arguments:
    ip_address -- an ip address as a string or an integer

    Returns:
    The IpRange object that match the passed in IP address; if not found return
    a default object that contains only "Unknowns".

    """
    _build_data()

    if isinstance(ip_address, int):
        ip = ip_address
    else:
        ip = ip_str_to_int(ip_address)

    # Perform a binary search to find the correct IpRange
    low = 0
    high = len(IP_TO_LOC) - 1

    while low <= high:
        mid = (low + high) >> 1
        entry = IP_TO_LOC[mid]

        if ip >= entry.start and ip <= entry.end:
            return entry
        elif ip < entry.start:
            high = mid - 1
        else:
            low = mid + 1

    # Default if we cannot find this IP in our dataset
    return NOT_FOUND_RANGE
