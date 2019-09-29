
import dramatiq
from dramatiq.brokers.redis import RedisBroker
dramatiq.set_broker(RedisBroker(host="redis", port=6379))

from apscheduler.schedulers.blocking import BlockingScheduler

import cron
import logging
import pytz
import signal
import sys  
import tasks  # imported for its side-effects


logging.basicConfig(
    format="[%(asctime)s] [PID %(process)d] [%(threadName)s] [%(name)s] [%(levelname)s] %(message)s",
    level=logging.INFO,
)


def main():
    scheduler = BlockingScheduler(timezone=pytz.timezone('Europe/London'))
    for trigger, job_name, func in cron.JOBS:
        # job_path = f"{module_path}:{func_name}.send"
        scheduler.add_job(func, trigger=trigger, name=job_name)

    def shutdown(signum, frame):
        scheduler.shutdown()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    scheduler.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())