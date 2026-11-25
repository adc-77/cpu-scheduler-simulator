"""
structures.py
-------------
Hand-built data structures used by the schedulers.
No built-in queue/heap/sort helpers are used on purpose.

Contents:
  1. Node + LinkedList   -> simple chain of nodes
  2. Queue               -> FIFO, built on a linked list (FCFS)
  3. CircularQueue       -> fixed-size FIFO using an array (Round Robin)
  4. MinHeap             -> priority queue (SJF, Priority scheduling)
  5. merge_sort          -> stable O(n log n) sort (sorting by arrival time)
"""


# ---------------------------------------------------------------
# 1. LINKED LIST
# ---------------------------------------------------------------
class Node:
    """One box in a linked list: holds data and a pointer to the next box."""

    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    """Singly linked list with a tail pointer so append is O(1)."""

    def __init__(self):
        self.head = None   # first node
        self.tail = None   # last node
        self._size = 0

    def is_empty(self):
        return self._size == 0

    def __len__(self):
        return self._size

    def append(self, data):
        """Add to the end. Time O(1)."""
        node = Node(data)
        if self.tail is None:          # list was empty
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self._size += 1

    def prepend(self, data):
        """Add to the front. Time O(1)."""
        node = Node(data)
        node.next = self.head
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1

    def remove_first(self):
        """Remove and return the first item. Time O(1)."""
        if self.head is None:
            raise IndexError("remove from empty LinkedList")
        node = self.head
        self.head = node.next
        if self.head is None:          # list became empty
            self.tail = None
        self._size -= 1
        return node.data

    def to_list(self):
        """Return items as a normal Python list. Time O(n)."""
        result = []
        current = self.head
        while current is not None:
            result.append(current.data)
            current = current.next
        return result


# ---------------------------------------------------------------
# 2. QUEUE (linked-list based, FIFO)
# ---------------------------------------------------------------
class Queue:
    """First In, First Out. Used by FCFS."""

    def __init__(self):
        self._list = LinkedList()

    def enqueue(self, item):
        """Add to the back. O(1)."""
        self._list.append(item)

    def dequeue(self):
        """Remove from the front. O(1)."""
        if self.is_empty():
            raise IndexError("dequeue from empty Queue")
        return self._list.remove_first()

    def peek(self):
        """Look at the front item without removing it. O(1)."""
        if self.is_empty():
            raise IndexError("peek from empty Queue")
        return self._list.head.data

    def is_empty(self):
        return self._list.is_empty()

    def size(self):
        return len(self._list)

    def to_list(self):
        return self._list.to_list()


# ---------------------------------------------------------------
# 3. CIRCULAR QUEUE (array based, fixed capacity)
# ---------------------------------------------------------------
class CircularQueue:
    """
    FIFO queue stored in a fixed-size array. When the end of the array
    is reached, the index wraps around to 0 using the % operator.
    Used by Round Robin (a process goes to the back after its time slice).
    """

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self.data = [None] * capacity
        self.front = 0     # index of the first item
        self.count = 0     # how many items are stored

    def is_empty(self):
        return self.count == 0

    def is_full(self):
        return self.count == self.capacity

    def size(self):
        return self.count

    def enqueue(self, item):
        """Add to the back, wrapping around the array. O(1)."""
        if self.is_full():
            raise OverflowError("CircularQueue is full")
        rear = (self.front + self.count) % self.capacity
        self.data[rear] = item
        self.count += 1

    def dequeue(self):
        """Remove from the front, wrapping around the array. O(1)."""
        if self.is_empty():
            raise IndexError("dequeue from empty CircularQueue")
        item = self.data[self.front]
        self.data[self.front] = None
        self.front = (self.front + 1) % self.capacity
        self.count -= 1
        return item

    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty CircularQueue")
        return self.data[self.front]

    def to_list(self):
        """Items from front to back. O(n)."""
        return [self.data[(self.front + i) % self.capacity]
                for i in range(self.count)]


# ---------------------------------------------------------------
# 4. MIN HEAP (priority queue)
# ---------------------------------------------------------------
class MinHeap:
    """
    Binary min-heap stored in a list.
    For the node at index i:
        parent = (i - 1) // 2,  left child = 2i + 1,  right child = 2i + 2
    The smallest item (by key) is always at index 0.

    key: a function that turns an item into something comparable.
         Tuples work great for tie-breaking, e.g.
         key=lambda p: (p["burst"], p["arrival"], p["pid"])
    """

    def __init__(self, key=None):
        self.items = []
        self.key = key if key is not None else (lambda x: x)

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)

    def peek(self):
        """Smallest item without removing it. O(1)."""
        if self.is_empty():
            raise IndexError("peek from empty MinHeap")
        return self.items[0]

    def push(self, item):
        """Insert an item. O(log n)."""
        self.items.append(item)
        self._sift_up(len(self.items) - 1)

    def pop(self):
        """Remove and return the smallest item. O(log n)."""
        if self.is_empty():
            raise IndexError("pop from empty MinHeap")
        smallest = self.items[0]
        last = self.items.pop()          # take the last item off the end
        if self.items:                   # put it at the root and fix order
            self.items[0] = last
            self._sift_down(0)
        return smallest

    def _less(self, i, j):
        """True if item at i should come before item at j."""
        return self.key(self.items[i]) < self.key(self.items[j])

    def _swap(self, i, j):
        self.items[i], self.items[j] = self.items[j], self.items[i]

    def _sift_up(self, i):
        """Move item up while it is smaller than its parent."""
        while i > 0:
            parent = (i - 1) // 2
            if self._less(i, parent):
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i):
        """Move item down while a child is smaller than it."""
        n = len(self.items)
        while True:
            left = 2 * i + 1
            right = 2 * i + 2
            smallest = i
            if left < n and self._less(left, smallest):
                smallest = left
            if right < n and self._less(right, smallest):
                smallest = right
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest


# ---------------------------------------------------------------
# 5. MERGE SORT
# ---------------------------------------------------------------
def merge_sort(items, key=None):
    """
    Stable merge sort. Returns a NEW sorted list.
    Stable = equal items keep their original order (good for ties).
    Time O(n log n), Space O(n).
    """
    if key is None:
        key = lambda x: x
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid], key)     # sort left half
    right = merge_sort(items[mid:], key)    # sort right half

    # Merge the two sorted halves
    merged = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):   # <= keeps it stable
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged
