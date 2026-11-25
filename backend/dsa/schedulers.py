"""
schedulers.py
-------------
CPU scheduling algorithms built on our own data structures.

Each process is a dict:
    {"pid": "P1", "arrival": 0, "burst": 5, "priority": 2}
(lower priority number = more important)

Every algorithm returns a dict:
    {
      "algorithm": "FCFS",
      "gantt": [{"pid": "P1", "start": 0, "end": 5}, ...],   # "IDLE" = CPU waiting
      "processes": [{... "completion", "turnaround", "waiting"}],
      "avg_waiting": 5.75,
      "avg_turnaround": 11.5
    }

Formulas:
    turnaround = completion - arrival
    waiting    = turnaround - burst
"""

import re

from dsa.structures import Queue, CircularQueue, MinHeap, merge_sort


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
MAX_TIME = 1000          # largest allowed arrival / burst / quantum (keeps the Gantt chart small)
PID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,20}$")   # letters, digits, _ . - (max 20 chars)


def to_int(value, label):
    """Convert a value to a whole number, or raise a clear ValueError."""
    if isinstance(value, bool):
        raise ValueError(label + " must be a whole number")
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(label + " must be a whole number")
        return int(value)
    try:
        return int(str(value).strip())
    except ValueError:
        raise ValueError(label + " must be a whole number")


def validate_processes(processes):
    """Check the input and return a clean copy with integer values."""
    if not processes:
        raise ValueError("Add at least one process")
    clean = []
    seen = set()
    for p in processes:
        pid = str(p.get("pid", "")).strip()
        if not PID_PATTERN.match(pid):
            raise ValueError("PID must be 1-20 characters: letters, digits, _ . or -")
        if pid in seen:
            raise ValueError("Duplicate PID: " + pid)
        seen.add(pid)
        arrival = to_int(p.get("arrival"), "Arrival time")
        burst = to_int(p.get("burst"), "Burst time")
        priority = to_int(p.get("priority", 0), "Priority")
        if arrival < 0:
            raise ValueError("Arrival time cannot be negative (" + pid + ")")
        if burst <= 0:
            raise ValueError("Burst time must be greater than 0 (" + pid + ")")
        if arrival > MAX_TIME or burst > MAX_TIME:
            raise ValueError("Arrival and burst time can be at most " + str(MAX_TIME))
        if abs(priority) > MAX_TIME:
            raise ValueError("Priority must be between -" + str(MAX_TIME) + " and " + str(MAX_TIME))
        clean.append({"pid": pid, "arrival": arrival,
                      "burst": burst, "priority": priority})
    return clean


def add_block(gantt, pid, start, end):
    """Add a Gantt block; merge it with the previous one if same PID and touching."""
    if gantt and gantt[-1]["pid"] == pid and gantt[-1]["end"] == start:
        gantt[-1]["end"] = end
    else:
        gantt.append({"pid": pid, "start": start, "end": end})


def build_result(name, processes, gantt, completion):
    """Compute turnaround/waiting for each process and the averages."""
    rows = []
    total_wait = 0
    total_turn = 0
    for p in processes:                      # keeps the user's original order
        done = completion[p["pid"]]
        turnaround = done - p["arrival"]
        waiting = turnaround - p["burst"]
        total_wait += waiting
        total_turn += turnaround
        rows.append({"pid": p["pid"], "arrival": p["arrival"],
                     "burst": p["burst"], "priority": p["priority"],
                     "completion": done, "turnaround": turnaround,
                     "waiting": waiting})
    n = len(processes)
    return {"algorithm": name, "gantt": gantt, "processes": rows,
            "avg_waiting": round(total_wait / n, 2),
            "avg_turnaround": round(total_turn / n, 2)}


# ---------------------------------------------------------------
# 1. FCFS - First Come, First Served (Queue)
# ---------------------------------------------------------------
def fcfs(processes):
    """Run processes in the order they arrive. Time O(n log n), Space O(n)."""
    procs = validate_processes(processes)
    ordered = merge_sort(procs, key=lambda p: p["arrival"])  # stable sort

    queue = Queue()
    for p in ordered:
        queue.enqueue(p)

    time = 0
    gantt = []
    completion = {}
    while not queue.is_empty():
        p = queue.dequeue()
        if time < p["arrival"]:                  # CPU idle until it arrives
            add_block(gantt, "IDLE", time, p["arrival"])
            time = p["arrival"]
        add_block(gantt, p["pid"], time, time + p["burst"])
        time += p["burst"]
        completion[p["pid"]] = time
    return build_result("FCFS", procs, gantt, completion)


# ---------------------------------------------------------------
# Shared engine for SJF and Priority (Min Heap, non-preemptive)
# ---------------------------------------------------------------
def _heap_schedule(name, processes, key):
    """
    Whenever the CPU is free:
      1. push every process that has arrived into a MinHeap
      2. pop the best one (smallest key) and run it to completion
    Time O(n log n), Space O(n).
    """
    procs = validate_processes(processes)
    ordered = merge_sort(procs, key=lambda p: p["arrival"])

    heap = MinHeap(key=key)
    i = 0                      # next process (by arrival) not yet in the heap
    n = len(ordered)
    time = 0
    gantt = []
    completion = {}

    while i < n or not heap.is_empty():
        # Move all arrived processes into the heap
        while i < n and ordered[i]["arrival"] <= time:
            heap.push(ordered[i])
            i += 1

        if heap.is_empty():                      # nobody ready: jump ahead
            next_arrival = ordered[i]["arrival"]
            add_block(gantt, "IDLE", time, next_arrival)
            time = next_arrival
            continue

        p = heap.pop()
        add_block(gantt, p["pid"], time, time + p["burst"])
        time += p["burst"]
        completion[p["pid"]] = time
    return build_result(name, procs, gantt, completion)


# ---------------------------------------------------------------
# 2. SJF - Shortest Job First (non-preemptive)
# ---------------------------------------------------------------
def sjf(processes):
    """Pick the ready process with the smallest burst. Ties: earlier arrival, then PID."""
    return _heap_schedule("SJF", processes,
                          key=lambda p: (p["burst"], p["arrival"], p["pid"]))


# ---------------------------------------------------------------
# 3. Priority Scheduling (non-preemptive, lower number = higher priority)
# ---------------------------------------------------------------
def priority_scheduling(processes):
    """Pick the ready process with the best priority. Ties: earlier arrival, then PID."""
    return _heap_schedule("PRIORITY", processes,
                          key=lambda p: (p["priority"], p["arrival"], p["pid"]))


# ---------------------------------------------------------------
# 4. Round Robin (Circular Queue)
# ---------------------------------------------------------------
def round_robin(processes, quantum):
    """
    Each process runs for at most `quantum` units, then goes to the back
    of the CircularQueue if it still has work left.
    Time O(n log n + total_burst / quantum), Space O(n).
    """
    procs = validate_processes(processes)
    quantum = to_int(quantum, "Time quantum")
    if quantum <= 0 or quantum > MAX_TIME:
        raise ValueError("Time quantum must be between 1 and " + str(MAX_TIME))

    ordered = merge_sort(procs, key=lambda p: p["arrival"])
    n = len(ordered)
    queue = CircularQueue(n)          # at most n processes can wait at once
    remaining = {p["pid"]: p["burst"] for p in ordered}

    i = 0
    time = 0
    gantt = []
    completion = {}

    # Put everything that has arrived at time 0 (or earlier) into the queue
    while i < n and ordered[i]["arrival"] <= time:
        queue.enqueue(ordered[i])
        i += 1

    while i < n or not queue.is_empty():
        if queue.is_empty():                     # CPU idle: jump to next arrival
            next_arrival = ordered[i]["arrival"]
            add_block(gantt, "IDLE", time, next_arrival)
            time = next_arrival
            while i < n and ordered[i]["arrival"] <= time:
                queue.enqueue(ordered[i])
                i += 1
            continue

        p = queue.dequeue()
        run = min(quantum, remaining[p["pid"]])
        add_block(gantt, p["pid"], time, time + run)
        time += run
        remaining[p["pid"]] -= run

        # New arrivals during this slice go in BEFORE the current process
        while i < n and ordered[i]["arrival"] <= time:
            queue.enqueue(ordered[i])
            i += 1

        if remaining[p["pid"]] > 0:
            queue.enqueue(p)                     # back of the line
        else:
            completion[p["pid"]] = time
    return build_result("RR", procs, gantt, completion)


# ---------------------------------------------------------------
# Dispatcher + comparison
# ---------------------------------------------------------------
def run_algorithm(name, processes, quantum=2):
    """Run one algorithm by name: FCFS, SJF, RR, PRIORITY."""
    name = name.upper()
    if name == "FCFS":
        return fcfs(processes)
    if name == "SJF":
        return sjf(processes)
    if name == "PRIORITY":
        return priority_scheduling(processes)
    if name == "RR":
        return round_robin(processes, quantum)
    raise ValueError("Unknown algorithm: " + name)


def compare_all(processes, quantum=2):
    """Run all four algorithms and report which has the lowest average waiting time."""
    results = [fcfs(processes), sjf(processes),
               priority_scheduling(processes), round_robin(processes, quantum)]
    summary = [{"algorithm": r["algorithm"],
                "avg_waiting": r["avg_waiting"],
                "avg_turnaround": r["avg_turnaround"]} for r in results]
    best = summary[0]
    for s in summary:
        if s["avg_waiting"] < best["avg_waiting"]:
            best = s
    return {"results": results, "summary": summary,
            "best_algorithm": best["algorithm"]}
