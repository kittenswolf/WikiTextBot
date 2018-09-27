# WikiTextBot made by https://github.com/kittenswolf
# Bot in action: reddit.com/u/WikiTextBot
# reddit.com/u/kittens_from_space

import subprocess
import time

wait_time_min = 30

wait_time_sec = wait_time_min * 60


def main():
    print("[INFO] Updating ban list...")
    p1 = subprocess.call(["python3", "update_ban_list.py"])
    print("[INFO] Deleting downvoted comments...")
    p2 = subprocess.call(["python3", "delete_downvoted.py"])

    print("[INFO] Sleeping...")
    time.sleep(wait_time_sec)


while True:
    try:
        main()
    except Exception as e:
        print("[ERROR]" + str(e))
