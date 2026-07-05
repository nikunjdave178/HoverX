import time


def retry(fn, attempts=3, base_delay=1.0):
    """Calls fn() with exponential backoff. Re-raises the last exception if
    every attempt fails."""
    for attempt in range(attempts):
        try:
            return fn()
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
