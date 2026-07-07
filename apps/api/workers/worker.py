import os

from rq import SimpleWorker, Worker
from rq.timeouts import TimerDeathPenalty

from services import redis_service
from tasks.queue import queue_names


def main() -> None:
    worker_class = SimpleWorker if os.name == "nt" else Worker
    if os.name == "nt":
        worker_class.death_penalty_class = TimerDeathPenalty
    worker_class(queue_names(), connection=redis_service.binary_client()).work()


if __name__ == "__main__":
    main()
