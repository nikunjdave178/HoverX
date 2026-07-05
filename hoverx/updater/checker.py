import sys

import requests
from packaging import version

from hoverx.updater.retry import retry
from hoverx.version import __version__

UPDATE_URL = "https://raw.githubusercontent.com/nikunjdave178/HoverX/main/update.json"


def check_for_update(timeout=3):
    try:
        resp = retry(lambda: requests.get(UPDATE_URL, timeout=timeout))
        resp.raise_for_status()
        data = resp.json()

        remote_version = version.parse(data.get("version", "0.0.0"))
        local_version = version.parse(__version__)

        if remote_version > local_version:
            return data

    except Exception as ex:
        if not getattr(sys, "frozen", False):
            print("Update check failed:", ex)
        return None

    return None
