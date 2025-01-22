import subprocess
import random
import numpy as np
import sys

events = np.array([])

with open('eventsPhotonic.txt') as f:
#with open('eventsPion.txt') as f:
    lines = f.readlines()
    for line in lines:
        events = np.append(events, int(line))

for i in range(100):
    event_id = events[i]
    print(f"Running event [{int(event_id)}]")
    subprocess.run(["python3", "unpacker_CEE.py", str(event_id)])
    subprocess.run(["python3", "unpacker_CEH.py", str(event_id)])
    subprocess.run(["python3", "towerSums.py"])
    subprocess.run(["python3", "plotTTs.py", str(event_id)])

print("All events completed!")
