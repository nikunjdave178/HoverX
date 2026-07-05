import os
import tempfile
import requests

from hoverx.updater.retry import retry


def download_update(url, timeout=10, on_progress=None):
    """
    Downloads update exe to a temp location.
    Returns full path to downloaded file.
    Raises exception on failure (including a truncated/incomplete download).

    on_progress, if given, is called as on_progress(downloaded, total) after
    each chunk; total is 0 if the server didn't send Content-Length.
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "HoverX")
    os.makedirs(temp_dir, exist_ok=True)

    target_path = os.path.join(temp_dir, "HoverX_new.exe")

    def attempt():
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0

            try:
                with open(target_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        if on_progress:
                            on_progress(downloaded, total)

                if total and downloaded != total:
                    raise IOError(
                        f"Incomplete download: got {downloaded} of {total} bytes"
                    )
            except Exception:
                # A network error mid-stream raises from inside the loop
                # above, before the size check below it - clean up the
                # partial file on any failure, not just a clean short read.
                if os.path.exists(target_path):
                    os.remove(target_path)
                raise

        return target_path

    return retry(attempt)
