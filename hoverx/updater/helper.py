import sys
import time
import os
import shutil
import subprocess

def main():
    if len(sys.argv) < 3:
        return

    target_exe = sys.argv[1]
    new_exe = sys.argv[2]
    backup = target_exe + ".bak"

    if not os.path.exists(new_exe):
        return

    # give main app time to exit
    time.sleep(1.5)

    try:
        # retry replace (Windows can hold locks briefly)
        for _ in range(10):  # ~5 seconds
            try:
                if os.path.exists(backup):
                    os.remove(backup)

                if os.path.exists(target_exe):
                    shutil.move(target_exe, backup)

                shutil.move(new_exe, target_exe)
                break
            except Exception:
                time.sleep(0.5)
        else:
            return  # could not replace

        # start updated app
        subprocess.Popen([target_exe], close_fds=True)

    except Exception:
        # restore backup if anything went wrong
        if os.path.exists(backup):
            shutil.move(backup, target_exe)

if __name__ == "__main__":
    main()
