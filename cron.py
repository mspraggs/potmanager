import importlib

from apscheduler.triggers.cron import CronTrigger

JOBS = []


def cron(crontab):
    """Wrap a Dramatiq actor in a cron schedule.
    """
    trigger = CronTrigger.from_crontab(crontab)

    def decorator(actor):
        job_name = f'{actor.fn.__module__}.{actor.fn.__name__}'
        JOBS.append((trigger, job_name, actor.send))
        return actor

    return decorator
