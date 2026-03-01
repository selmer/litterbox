import tinytuya
import time
import json

##Polls the litterbox for output

d = tinytuya.OutletDevice(
    dev_id="bfb69fa0d9a31595751qfz",
    address="192.168.68.110",
    local_key="@4XOjSgO$r/sqZG:",
    version=3.4
)

d.set_socketPersistent(True)

KNOWN_DPS = {
    "6":  "cat_weight (raw, ÷1000 = kg)",
    "7":  "excretion_times_day",
    "8":  "excretion_time_day (seconds)",
    "17": "deodorization",
    "22": "fault",
}

print("👀 Watching for changes... (Ctrl+C to stop)\n")

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
            print(f"⏰ {time.strftime('%H:%M:%S')} — Changes detected:")
            for dp, change in changes.items():
                label = KNOWN_DPS.get(dp, f"DP {dp} (unknown)")
                print(f"  [{dp}] {label}: {change['old']} → {change['new']}")
            print()

    except Exception as e:
        print(f"⚠️  Error: {e}")

    time.sleep(5)
