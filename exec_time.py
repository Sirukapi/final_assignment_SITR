
import os
import numpy as np

open("output.txt", "w").close()

N = 100

for i in range(N):
    os.system("{ time ./multiply; } 2>&1 | grep -oP '^[\\d.]+(?=user)' >> output.txt")

with open("output.txt", "r") as f:
    times = [float(line.strip()) for line in f.readlines()]

print(f"Nombre de runs :{N}")
Q1, Q2, Q3 = np.quantile(times, [0.25, 0.5, 0.75])
print(f"Minimum :{np.min(times)}s")
print(f"Q1 : {Q1}s")
print(f"Q2 : {Q2}s")
print(f"Q3 : {Q3}s")
print(f"Maximum :{np.max(times)}s")
print(f"WCET : {np.max(times)*1.2}s")
