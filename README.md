# CPU Process Scheduling Simulator

A beginner-friendly DSA project that simulates how an operating system schedules processes on the CPU.
The scheduling logic is built on **our own** data structures (Queue, Circular Queue, Min Heap, Linked List, Merge Sort) and not on Python's built-in `queue`, `heapq` or `sort`.

**Tech stack:** Python (Flask) &bull; SQLite (`sqlite3`) &bull; plain HTML, CSS, JavaScript

## Features

- Add, edit, view and delete processes (PID, arrival time, burst time, priority)
- Algorithms: **FCFS**, **SJF**, **Priority**, **Round Robin** (with time quantum)
- Gantt chart, waiting time, turnaround time and averages for each run
- **Compare All** button: runs all four algorithms and shows the best one
- Processes and every simulation run are saved in SQLite, so they survive page reloads and restarts

## Project Structure

```
cpu-scheduler-simulator/
├── README.md
├── .gitignore
├── backend/
│   ├── dsa/
│   │   ├── structures.py     # LinkedList, Queue, CircularQueue, MinHeap, merge_sort
│   │   └── schedulers.py     # FCFS, SJF, Priority, Round Robin, compare_all
│   ├── db/
│   │   └── database.py       # all SQLite code
│   ├── app.py                # Flask API (also serves the frontend)
│   └── test_dsa.py           # unit tests for the DSA code
└── frontend/
    ├── index.html
    ├── styles.css
    └── app.js
```

## Setup and Run

You need **Python 3.8+**. Run these commands from the project root.

**Windows (Command Prompt / PowerShell)**
```
cd cpu-scheduler-simulator
python -m venv venv
venv\Scripts\activate
pip install flask
cd backend
python test_dsa.py
python app.py
```

**macOS / Linux**
```
cd cpu-scheduler-simulator
python3 -m venv venv
source venv/bin/activate
pip install flask
cd backend
python test_dsa.py
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.
(`python test_dsa.py` should print `OK`. Run the tests before the app.)

The database file `backend/db/scheduler.db` is created automatically on the first run.

## How to Use

1. Click **Load Sample Data** (or add your own processes).
2. Choose an algorithm (for Round Robin, set the time quantum) and click **Run Algorithm**.
3. Click **Compare All** to see all four algorithms side by side.
4. Past runs appear in **Run History**. Click **View** to reopen one.

## API Endpoints

| Method | URL | What it does |
|--------|-----|--------------|
| GET | `/api/processes` | List processes |
| POST | `/api/processes` | Add a process |
| PUT | `/api/processes/<pid>` | Edit a process |
| DELETE | `/api/processes/<pid>` | Delete one process |
| DELETE | `/api/processes` | Delete all processes |
| POST | `/api/processes/sample` | Load 4 sample processes |
| POST | `/api/simulate` | Run one algorithm `{algorithm, quantum}` |
| POST | `/api/compare` | Run all algorithms `{quantum}` |
| GET | `/api/runs` | List saved runs |
| GET | `/api/runs/<id>` | Get one saved run with its Gantt chart |
| DELETE | `/api/runs` | Clear run history |

## Rules Used by the Simulator

- `turnaround time = completion time - arrival time`
- `waiting time = turnaround time - burst time`
- **SJF** and **Priority** are **non-preemptive** (a running process is never interrupted).
- **Priority:** a *lower number means higher priority*.
- Ties: **SJF** and **Priority** pick the earlier arrival, then the smaller PID (text order, so `P10` comes before `P2`). **FCFS** and **Round Robin** keep the order the processes were entered.
- Input limits: PID is 1-20 characters (letters, digits, `_ . -`); arrival, burst and quantum are whole numbers up to 1000; burst and quantum must be at least 1.
- If the CPU has nothing to run, the Gantt chart shows an `IDLE` block.
- **Round Robin:** processes that arrive during a time slice join the queue *before* the process that just used its slice.

### Sample Check (P1: 0/5, P2: 1/3, P3: 2/8, P4: 3/6, quantum = 3)

| Algorithm | Avg Waiting | Avg Turnaround |
|-----------|-------------|----------------|
| FCFS | 5.75 | 11.25 |
| SJF | 5.25 | 10.75 |
| Priority | 5.25 | 10.75 |
| Round Robin | 8.5 | 14.0 |

## Where Each DSA Concept Is Used

| Data structure / algorithm | Used for |
|----------------------------|----------|
| Linked List | Storage behind the Queue |
| Queue (FIFO) | FCFS ready queue |
| Circular Queue | Round Robin ready queue (wraps around with `%`) |
| Min Heap (Priority Queue) | SJF (smallest burst) and Priority (best priority) |
| Merge Sort | Sorting processes by arrival time (stable) |

## Time and Space Complexity

`n` = number of processes.

### Data Structures

| Structure | Operation | Time | Space |
|-----------|-----------|------|-------|
| Linked List | append / prepend / remove_first | O(1) | O(n) |
| Linked List | to_list | O(n) | |
| Queue | enqueue / dequeue / peek | O(1) | O(n) |
| Circular Queue | enqueue / dequeue / peek | O(1) | O(capacity) |
| Min Heap | push / pop | O(log n) | O(n) |
| Min Heap | peek | O(1) | |
| Merge Sort | sort | O(n log n) | O(n) |

### Scheduling Algorithms

| Algorithm | Time | Space | Why |
|-----------|------|-------|-----|
| FCFS | O(n log n) | O(n) | Merge sort by arrival, then n O(1) queue operations |
| SJF | O(n log n) | O(n) | Merge sort, then n heap pushes and n heap pops at O(log n) each |
| Priority | O(n log n) | O(n) | Same as SJF with a different heap key |
| Round Robin | O(n log n + S) | O(n + S) | Sort, then each time slice costs O(1). S = number of slices, at most (total burst time / quantum) + n |

Computing the metrics is O(n). The Gantt chart has O(n) blocks for FCFS/SJF/Priority and up to S blocks for Round Robin, which is why Round Robin's space includes S.

## Team and Workflow Notes

Suggested split for a team of 3 to 4:

| Member | Files |
|--------|-------|
| 1 | `backend/dsa/structures.py`, `backend/test_dsa.py` |
| 2 | `backend/dsa/schedulers.py` |
| 3 | `backend/app.py`, `backend/db/database.py` |
| 4 | `frontend/` files, `README.md` |

Git workflow:

```
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

- Each member works on their own branch (`git checkout -b feature-name`), then opens a pull request into `main`.
- Run `python test_dsa.py` before every commit.
- Never commit `venv/` or `scheduler.db` (already in `.gitignore`).

## Possible Viva Questions

- **Why a Min Heap for SJF?** It gives the shortest job in O(log n) instead of scanning all processes in O(n) every time.
- **Why a Circular Queue for Round Robin?** Processes keep rotating to the back of the line, and a circular array reuses freed slots without shifting elements.
- **Why Merge Sort?** It is O(n log n) and stable, so processes with equal arrival times keep their input order.
- **What is the convoy effect?** In FCFS, one long process at the front makes all short processes behind it wait.
- **Which algorithm can cause starvation?** SJF and Priority: long or low-priority jobs may wait forever if shorter or higher-priority jobs keep arriving.

## Limitations / Ideas to Extend

- SJF and Priority are non-preemptive. Preemptive versions (SRTF) would be a good extension.
- Add aging to Priority scheduling to prevent starvation.
- Add CSV export for results.
