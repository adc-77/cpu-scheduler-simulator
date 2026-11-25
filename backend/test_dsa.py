"""
test_dsa.py
-----------
Tests for our data structures and scheduling algorithms.
Run from the backend/ folder:

    python test_dsa.py

No extra libraries needed (uses Python's built-in unittest).
"""

import unittest

from dsa.structures import LinkedList, Queue, CircularQueue, MinHeap, merge_sort
from dsa.schedulers import (fcfs, sjf, priority_scheduling, round_robin,
                            run_algorithm, compare_all)


def sample_processes():
    """Same 4 processes used in most tests (hand-calculated answers below)."""
    return [
        {"pid": "P1", "arrival": 0, "burst": 5, "priority": 2},
        {"pid": "P2", "arrival": 1, "burst": 3, "priority": 1},
        {"pid": "P3", "arrival": 2, "burst": 8, "priority": 4},
        {"pid": "P4", "arrival": 3, "burst": 6, "priority": 3},
    ]


def gantt_order(result):
    """Turn a Gantt chart into [(pid, start, end), ...] for easy comparing."""
    return [(g["pid"], g["start"], g["end"]) for g in result["gantt"]]


# ---------------------------------------------------------------
# DATA STRUCTURE TESTS
# ---------------------------------------------------------------
class TestLinkedList(unittest.TestCase):
    def test_append_prepend_remove(self):
        ll = LinkedList()
        self.assertTrue(ll.is_empty())
        ll.append(2)
        ll.append(3)
        ll.prepend(1)
        self.assertEqual(ll.to_list(), [1, 2, 3])
        self.assertEqual(len(ll), 3)
        self.assertEqual(ll.remove_first(), 1)
        self.assertEqual(ll.to_list(), [2, 3])

    def test_remove_until_empty_then_append(self):
        ll = LinkedList()
        ll.append("a")
        ll.remove_first()
        self.assertTrue(ll.is_empty())
        ll.append("b")                      # tail must have been reset
        self.assertEqual(ll.to_list(), ["b"])

    def test_remove_from_empty(self):
        with self.assertRaises(IndexError):
            LinkedList().remove_first()


class TestQueue(unittest.TestCase):
    def test_fifo_order(self):
        q = Queue()
        for x in [1, 2, 3]:
            q.enqueue(x)
        self.assertEqual(q.peek(), 1)
        self.assertEqual(q.size(), 3)
        self.assertEqual([q.dequeue(), q.dequeue(), q.dequeue()], [1, 2, 3])
        self.assertTrue(q.is_empty())

    def test_dequeue_empty(self):
        with self.assertRaises(IndexError):
            Queue().dequeue()


class TestCircularQueue(unittest.TestCase):
    def test_fifo_and_full(self):
        cq = CircularQueue(3)
        for x in "abc":
            cq.enqueue(x)
        self.assertTrue(cq.is_full())
        with self.assertRaises(OverflowError):
            cq.enqueue("d")
        self.assertEqual(cq.dequeue(), "a")

    def test_wrap_around(self):
        cq = CircularQueue(3)
        for x in "abc":
            cq.enqueue(x)
        cq.dequeue()                        # remove "a"
        cq.enqueue("d")                     # reuses the freed slot 0
        self.assertEqual(cq.to_list(), ["b", "c", "d"])
        self.assertEqual(cq.peek(), "b")

    def test_empty_errors(self):
        cq = CircularQueue(2)
        self.assertTrue(cq.is_empty())
        with self.assertRaises(IndexError):
            cq.dequeue()

    def test_bad_capacity(self):
        with self.assertRaises(ValueError):
            CircularQueue(0)


class TestMinHeap(unittest.TestCase):
    def test_pops_in_sorted_order(self):
        h = MinHeap()
        for x in [5, 3, 8, 1, 9, 2, 7]:
            h.push(x)
        self.assertEqual(h.peek(), 1)
        result = []
        while not h.is_empty():
            result.append(h.pop())
        self.assertEqual(result, [1, 2, 3, 5, 7, 8, 9])

    def test_custom_key_and_tie_break(self):
        h = MinHeap(key=lambda p: (p["burst"], p["pid"]))
        h.push({"pid": "B", "burst": 2})
        h.push({"pid": "A", "burst": 2})
        h.push({"pid": "C", "burst": 1})
        self.assertEqual([h.pop()["pid"] for _ in range(3)], ["C", "A", "B"])

    def test_pop_empty(self):
        with self.assertRaises(IndexError):
            MinHeap().pop()


class TestMergeSort(unittest.TestCase):
    def test_sorts(self):
        self.assertEqual(merge_sort([4, 1, 3, 2, 5]), [1, 2, 3, 4, 5])
        self.assertEqual(merge_sort([]), [])
        self.assertEqual(merge_sort([7]), [7])

    def test_does_not_change_original(self):
        original = [3, 1, 2]
        merge_sort(original)
        self.assertEqual(original, [3, 1, 2])

    def test_stable(self):
        items = [("a", 1), ("b", 1), ("c", 0)]
        result = merge_sort(items, key=lambda x: x[1])
        self.assertEqual(result, [("c", 0), ("a", 1), ("b", 1)])


# ---------------------------------------------------------------
# SCHEDULING ALGORITHM TESTS (answers calculated by hand)
# ---------------------------------------------------------------
class TestFCFS(unittest.TestCase):
    def test_sample(self):
        r = fcfs(sample_processes())
        self.assertEqual(gantt_order(r), [("P1", 0, 5), ("P2", 5, 8),
                                          ("P3", 8, 16), ("P4", 16, 22)])
        self.assertEqual(r["avg_waiting"], 5.75)
        self.assertEqual(r["avg_turnaround"], 11.25)

    def test_unsorted_input(self):
        procs = list(reversed(sample_processes()))
        self.assertEqual(gantt_order(fcfs(procs))[0][0], "P1")

    def test_idle_gap(self):
        r = fcfs([{"pid": "A", "arrival": 3, "burst": 2, "priority": 0}])
        self.assertEqual(gantt_order(r), [("IDLE", 0, 3), ("A", 3, 5)])
        self.assertEqual(r["processes"][0]["waiting"], 0)


class TestSJF(unittest.TestCase):
    def test_sample(self):
        r = sjf(sample_processes())
        self.assertEqual(gantt_order(r), [("P1", 0, 5), ("P2", 5, 8),
                                          ("P4", 8, 14), ("P3", 14, 22)])
        self.assertEqual(r["avg_waiting"], 5.25)
        self.assertEqual(r["avg_turnaround"], 10.75)

    def test_idle_gap_then_shortest(self):
        procs = [{"pid": "A", "arrival": 0, "burst": 2, "priority": 0},
                 {"pid": "B", "arrival": 10, "burst": 5, "priority": 0},
                 {"pid": "C", "arrival": 10, "burst": 1, "priority": 0}]
        r = sjf(procs)
        self.assertEqual(gantt_order(r), [("A", 0, 2), ("IDLE", 2, 10),
                                          ("C", 10, 11), ("B", 11, 16)])


class TestPriority(unittest.TestCase):
    def test_sample(self):
        r = priority_scheduling(sample_processes())
        self.assertEqual(gantt_order(r), [("P1", 0, 5), ("P2", 5, 8),
                                          ("P4", 8, 14), ("P3", 14, 22)])

    def test_lower_number_wins(self):
        procs = [{"pid": "A", "arrival": 0, "burst": 3, "priority": 5},
                 {"pid": "B", "arrival": 0, "burst": 3, "priority": 1}]
        self.assertEqual(gantt_order(priority_scheduling(procs))[0][0], "B")


class TestRoundRobin(unittest.TestCase):
    def test_sample_quantum_3(self):
        r = round_robin(sample_processes(), 3)
        self.assertEqual(gantt_order(r), [
            ("P1", 0, 3), ("P2", 3, 6), ("P3", 6, 9), ("P4", 9, 12),
            ("P1", 12, 14), ("P3", 14, 17), ("P4", 17, 20), ("P3", 20, 22)])
        self.assertEqual(r["avg_waiting"], 8.5)
        self.assertEqual(r["avg_turnaround"], 14.0)

    def test_big_quantum_acts_like_fcfs(self):
        rr = round_robin(sample_processes(), 100)
        ff = fcfs(sample_processes())
        self.assertEqual(gantt_order(rr), gantt_order(ff))

    def test_idle_gap(self):
        procs = [{"pid": "A", "arrival": 0, "burst": 1, "priority": 0},
                 {"pid": "B", "arrival": 5, "burst": 2, "priority": 0}]
        r = round_robin(procs, 2)
        self.assertEqual(gantt_order(r), [("A", 0, 1), ("IDLE", 1, 5), ("B", 5, 7)])

    def test_bad_quantum(self):
        with self.assertRaises(ValueError):
            round_robin(sample_processes(), 0)


class TestValidationAndCompare(unittest.TestCase):
    def test_bad_input(self):
        with self.assertRaises(ValueError):
            fcfs([])
        with self.assertRaises(ValueError):          # duplicate PID
            fcfs([{"pid": "A", "arrival": 0, "burst": 1},
                  {"pid": "A", "arrival": 1, "burst": 1}])
        with self.assertRaises(ValueError):          # burst must be > 0
            fcfs([{"pid": "A", "arrival": 0, "burst": 0}])
        with self.assertRaises(ValueError):          # negative arrival
            fcfs([{"pid": "A", "arrival": -1, "burst": 1}])

    def test_pid_rules(self):
        for bad in ["", "   ", 'a"b', "a/b", "a b", "x" * 21]:
            with self.assertRaises(ValueError):
                fcfs([{"pid": bad, "arrival": 0, "burst": 1}])
        fcfs([{"pid": "P-1_a.b", "arrival": 0, "burst": 1}])   # allowed characters

    def test_number_rules(self):
        bad_values = [
            {"arrival": "abc", "burst": 1},        # not a number
            {"arrival": 0, "burst": 2.5},          # not a whole number
            {"arrival": None, "burst": 1},         # missing
            {"arrival": 0, "burst": 1001},         # above the limit
            {"arrival": 0, "burst": 1, "priority": "x"},
        ]
        for values in bad_values:
            with self.assertRaises(ValueError):
                fcfs([dict(pid="A", **values)])
        # whole-number strings and floats like 3.0 are accepted
        r = fcfs([{"pid": "A", "arrival": "1", "burst": 2.0, "priority": "3"}])
        self.assertEqual(r["processes"][0]["completion"], 3)

    def test_quantum_limits(self):
        with self.assertRaises(ValueError):
            round_robin(sample_processes(), "abc")
        with self.assertRaises(ValueError):
            round_robin(sample_processes(), 5000)

    def test_run_algorithm_names(self):
        for name in ["FCFS", "sjf", "Priority", "rr"]:
            r = run_algorithm(name, sample_processes(), 3)
            self.assertEqual(len(r["processes"]), 4)
        with self.assertRaises(ValueError):
            run_algorithm("LOL", sample_processes())

    def test_compare_all(self):
        c = compare_all(sample_processes(), 3)
        self.assertEqual(len(c["results"]), 4)
        self.assertEqual(len(c["summary"]), 4)
        self.assertIn(c["best_algorithm"], ["SJF", "PRIORITY"])  # both 5.25

    def test_waiting_never_negative(self):
        for name in ["FCFS", "SJF", "PRIORITY", "RR"]:
            r = run_algorithm(name, sample_processes(), 2)
            for row in r["processes"]:
                self.assertGreaterEqual(row["waiting"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
