from abc import abstractmethod
from queue import PriorityQueue
from typing import Any, Tuple


class BaseJobQueue:
    def __init__(self):
        self._queue

    @abstractmethod
    def put(self, job, priority):
        pass

    @abstractmethod
    def get(self) -> Tuple[int, Any]:
        pass

    @abstractmethod
    def empty(self) -> bool:
        pass


class PriorityJobQueue(BaseJobQueue):
    def __init__(self):
        self._queue = PriorityQueue()

    def put(self, job, priority):
        self._queue.put((priority, job))

    def get(self) -> Tuple[int, Any]:
        return self._queue.get()

    def empty(self) -> bool:
        return self._queue.empty()
