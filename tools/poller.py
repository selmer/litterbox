import os
import time

import tinytuya
from dotenv import load_dotenv

load_dotenv()

## Polls the litterbox for output

dev_id = os.environ["TUYA_DEV_ID"]
address = os.environ["TUYA_ADDRESS"]
local_key = os.environ["TUYA_LOCAL_KEY"]
version = float(os.environ.get("TUYA_VERSION", "3.4"))

d = tinytuya.OutletDevice(
    dev_id=dev_id,
    address=address,
    local_key=local_key,
    version=version,
)

d.set_socketPersistent(True)

KNOWN_DPS = {
    "6":  "cat_weight (raw, ÷1000 = kg)",
    "7":  "excretion_times_day",
    "8":  "excretion_time_day (seconds)",
    "17": "deodorization",
    "22": "fault",
}

print("Watching for changes... (Ctrl+C to stop)\n")

previous = {}

while True:
    try:
        data = d.status()
        dps = data.get("dps", {})

        changes = {}
        for k, v in dps.items():
            if previous.get(k) != v:
                changes[k] = {"old": previous.get(k, "?"), "new": v}
                previous[k] = v

        if changes:
            print(f"{time.strftime('%H:%M:%S')} — Changes detected:")
            for dp, change in changes.items():
                label = KNOWN_DPS.get(dp, f"DP {dp} (unknown)")
                print(f"  [{dp}] {label}: {change['old']} -> {change['new']}")
            print()

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(5)
