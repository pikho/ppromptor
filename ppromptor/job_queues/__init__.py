from abc import abstractmethod
from queue import PriorityQueue
from typing import Any, Tuple

from ppromptor.base.schemas import TABLE_MAP, Command
from sqlalchemy import column


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

    @abstractmethod
    def done(self, cmd, state_code: int) -> None:
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

    def done(self, cmd, state_code: int) -> None:
        return None


class ORMJobQueue(BaseJobQueue):
    def __init__(self, session):
        self._sess = session

    def _serialize_data(self, data):
        res = {}

        for key, value in data.items():
            if value is None:
                rec = None
            elif isinstance(value, list):
                rec = {
                    "cls": value[0].__class__.__name__,
                    "value": [x.id for x in value]
                }
            else:
                rec = {
                    "cls": value.__class__.__name__,
                    "value": value.id
                }

            res[key] = rec

        return res

    def _deserialize_data(self, data):
        res = {}
        # breakpoint()
        for key, value in data.items():
            if value is None:
                rec = None
            elif isinstance(value["value"], list):
                table = TABLE_MAP[value["cls"]]
                rec = self._sess.query(table).filter(table.id.in_(value["value"])).all()
            else:
                table = TABLE_MAP[value["cls"]]
                rec = self._sess.query(table).filter(table.id == value["value"]).first()
            res[key] = rec
        return res

    def put(self, job, priority):
        _job = Command(cmd={"cmd": job["cmd"]},
                       data=self._serialize_data(job["data"]),
                       owner="user",
                       priority=priority,
                       state=0)
        self._sess.add(_job)
        self._sess.commit()

    def get(self) -> Tuple[int, Any]:
        cmd = (self._sess.query(Command)
               .filter_by(state=0)
               .order_by(Command.priority.asc())
               .first())
        cmd.state = 1
        self._sess.add(cmd)
        self._sess.commit()

        job = {
            "id": cmd.id,
            "cmd": cmd.cmd["cmd"],
            "data": self._deserialize_data(cmd.data),
            "orig_obj": cmd
        }
        return (cmd.priority, job)

    def empty(self) -> bool:
        count = (self._sess.query(Command)
                 .filter_by(state=0)
                 .order_by(Command.priority.asc())
                 .count())
        return count == 0

    def done(self, cmd, state_code: int) -> None:
        cmd = cmd["orig_obj"]
        cmd.state = state_code
        self._sess.add(cmd)
        self._sess.commit()
