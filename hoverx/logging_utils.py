import os


def log(msg: str):
    """Very simple, best-effort file logger safe to call from a frozen exe."""
    try:
        with open(os.path.join(os.getenv("TEMP"), "hoverx.log"), "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass
