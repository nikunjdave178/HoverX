import os
import tempfile
import requests

def download_update(url, timeout=10):
    """
    Downloads update exe to a temp location.
    Returns full path to downloaded file.
    Raises exception on failure.
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "HoverX")
    os.makedirs(temp_dir, exist_ok=True)

    target_path = os.path.join(temp_dir, "HoverX_new.exe")

    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return target_path
