from math import gcd
from functools import reduce
import copy


# ---------------------------------------------------------------------------
# Useful functions
# ---------------------------------------------------------------------------

def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def lcm_list(lst: list) -> int:
    return reduce(lcm, lst)



C1 = 1.32 #WCET

TASKS = [
    ("tau1", C1, 10),
    ("tau2", 3,  10),
    ("tau3", 2,  20),
    ("tau4", 2,  20),
    ("tau5", 2,  40),
    ("tau6", 2,  40),
    ("tau7", 3,  80),
]


# ---------------------------------------------------------------------------
# Step 1 — Schedulability check (utilisation bound)
# ---------------------------------------------------------------------------

def check_utilisation(tasks: list) -> float:
    U = sum(c / t for _, c, t in tasks)
    print("=" * 60)
    print("SCHEDULABILITY CHECK")
    print("=" * 60)
    print(f"  {'Task':<8} {'C':>4} {'T':>6} {'U_i':>8}")
    for name, c, t in tasks:
        print(f"  {name:<8} {c:>4} {t:>6} {c/t:>8.4f}")
    print(f"  {'TOTAL':<8} {'':>4} {'':>6} {U:>8.4f}")
    feasible = U <= 1.0
    print(f"\n  U = {U:.4f} {'<= 1  =>  Necessary condition MET' if feasible else '> 1  =>  NOT schedulable'}")
    return U


# ---------------------------------------------------------------------------
# Step 2 — Generate all jobs in [0, H)
# ---------------------------------------------------------------------------

def generate_jobs(tasks: list, H: int) -> list:
    jobs = []
    for name, c, period in tasks:
        for k in range(H // period):
            jobs.append({
                "task":     name,
                "c":        c,
                "period":   period,
                "release":  k * period,
                "deadline": (k + 1) * period,
                "job_idx":  k + 1,
            })
    jobs.sort(key=lambda j: j["release"])
    return jobs


# ---------------------------------------------------------------------------
# Step 3 — Non-preemptive EDF + SJF scheduler
# ---------------------------------------------------------------------------

def simulate(job_list: list, allow_miss_task: str = None) -> dict:
    remaining = copy.deepcopy(job_list)
    pending   = []
    schedule  = []
    time      = 0

    while remaining or pending:
        # Admit newly released jobs into the pending queue
        new_arrivals = [j for j in remaining if j["release"] <= time]
        for j in new_arrivals:
            pending.append(j)
            remaining.remove(j)

        if not pending:
            # CPU idle — jump to next release
            next_release = min(j["release"] for j in remaining)
            time = next_release
            continue

        # EDF + SJF tie-break
        pending.sort(key=lambda j: (j["deadline"], j["c"]))
        job = pending.pop(0)

        # If this job will miss its deadline and it is not the allowed task,
        # try to find an alternative job in the pending queue that won't miss.
        if time + job["c"] > job["deadline"] and job["task"] != allow_miss_task:
            alt = next(
                (j for j in pending if time + j["c"] <= j["deadline"]),
                None
            )
            if alt:
                pending.append(job)   # put back
                pending.remove(alt)
                job = alt

        start  = time
        finish = time + job["c"]
        wait   = start - job["release"]
        time   = finish

        schedule.append({
            "task":     job["task"],
            "job_idx":  job["job_idx"],
            "release":  job["release"],
            "start":    start,
            "finish":   finish,
            "deadline": job["deadline"],
            "wait":     wait,
            "response": finish - job["release"],
            "missed":   finish > job["deadline"],
        })

    total_busy = sum(j["c"] for j in job_list)
    H          = max(j["deadline"] for j in job_list)
    total_idle = H - total_busy
    total_wait = sum(j["wait"] for j in schedule)
    feasible   = all(not j["missed"] for j in schedule)

    return {
        "schedule":   schedule,
        "feasible":   feasible,
        "total_wait": total_wait,
        "total_idle": total_idle,
        "total_busy": total_busy,
    }


# ---------------------------------------------------------------------------
# Step 4 — Response-time analysis (recurrence from assignment)
#   R^n_i = C_i + max(R^{n-1}_i - (a^n_i - a^{n-1}_i), 0)
# ---------------------------------------------------------------------------

def response_time_analysis(schedule: list, tasks: list):
    print("\n" + "=" * 60)
    print("RESPONSE-TIME ANALYSIS")
    print("=" * 60)
    print(f"  Formula: R^n_i = C_i + max(R^{{n-1}}_i - (a^n_i - a^{{n-1}}_i), 0)")
    print()
    print(f"  {'Task':<8} {'Job':>4} {'Release':>8} {'C_i':>5} {'R^n':>6} {'D_i':>6}  OK?")
    print("  " + "-" * 50)

    task_last_R  = {}  # previous response time per task
    task_last_a  = {}  # previous release time per task
    task_wcet    = {name: c for name, c, _ in tasks}
    task_period  = {name: t for name, _, t in tasks}

    for entry in schedule:
        name = entry["task"]
        a_n  = entry["release"]
        c    = task_wcet[name]
        D_i  = task_period[name]

        if name not in task_last_R:
            # First job: no predecessor
            R_n = c
        else:
            R_prev = task_last_R[name]
            a_prev = task_last_a[name]
            R_n = c + max(R_prev - (a_n - a_prev), 0)

        task_last_R[name] = R_n
        task_last_a[name] = a_n

        ok = "yes" if R_n <= D_i else "NO !"
        print(f"  {name:<8} {entry['job_idx']:>4} {a_n:>8} {c:>5} {R_n:>6} {D_i:>6}  {ok}")


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

def print_schedule(result: dict, title: str):
    sched = result["schedule"]
    print("\n" + "=" * 60)
    print(f"SCHEDULE — {title}")
    print("=" * 60)
    print(f"  {'Task':<8} {'Job':>4} {'Rel':>5} {'Start':>6} {'End':>5} {'DL':>5} {'Wait':>5} {'Miss':>5}")
    print("  " + "-" * 55)
    for j in sched:
        missed_str = "YES" if j["missed"] else "-"
        print(f"  {j['task']:<8} {j['job_idx']:>4} {j['release']:>5} "
              f"{j['start']:>6} {j['finish']:>5} {j['deadline']:>5} "
              f"{j['wait']:>5} {missed_str:>5}")

    print()
    print(f"  Feasible       : {result['feasible']}")
    print(f"  Total busy     : {result['total_busy']}")
    print(f"  Total idle     : {result['total_idle']}")
    print(f"  Total waiting  : {result['total_wait']}")
    print(f"  Busy + Idle    : {result['total_busy']} + {result['total_idle']} "
          f"= {result['total_busy'] + result['total_idle']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # --- Hyperperiod ---
    H = lcm_list([t for _, _, t in TASKS])
    print(f"Hyperperiod H = lcm({[t for _,_,t in TASKS]}) = {H}\n")

    # --- 1. Utilisation check ---
    U = check_utilisation(TASKS)

    if U > 1.0:
        print("\nTask set is NOT schedulable. Exiting.")
        exit(1)

    # --- 2. Generate jobs ---
    jobs = generate_jobs(TASKS, H)
    print(f"\nTotal jobs in hyperperiod: {len(jobs)}")

    # --- 3a. Schedule — no missed deadlines ---
    result_a = simulate(jobs)
    print_schedule(result_a, "No missed deadlines (minimise waiting time)")

    # --- 3b. Response-time analysis ---
    response_time_analysis(result_a["schedule"], TASKS)

    # --- 4. Verify idle time maximisation ---
    print("\n" + "=" * 60)
    print("IDLE TIME VERIFICATION")
    print("=" * 60)
    print(f"  Minimising waiting time <=> maximising idle time")
    print(f"  Total idle time = H - sum(C_i * (H/T_i))")
    print(f"                  = {H} - {result_a['total_busy']} = {result_a['total_idle']}")
    print(f"  This is the theoretical maximum idle time (fixed by the task set).")

    # --- 5. Schedule — tau5 allowed to miss ---
    result_b = simulate(jobs, allow_miss_task="tau5")
    print_schedule(result_b, "tau5 allowed to miss a deadline")

    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"  Waiting time (no miss)   : {result_a['total_wait']}")
    print(f"  Waiting time (tau5 miss) : {result_b['total_wait']}")
    delta = result_a['total_wait'] - result_b['total_wait']
    print(f"  Improvement              : {delta} time units")
    missed = [j for j in result_b['schedule'] if j['missed']]
    print(f"  Missed deadlines (tau5)  : {len(missed)} job(s)")
    for j in missed:
        print(f"    -> {j['task']} job {j['job_idx']}: "
              f"finished at {j['finish']}, deadline was {j['deadline']}")
