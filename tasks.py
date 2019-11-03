import datetime
import logging

import dramatiq
from dramatiq.brokers.redis import RedisBroker
dramatiq.set_broker(RedisBroker(host='redis', port=6379))
import redis

from cron import cron
import monzo


logging.basicConfig(
    format=(
        '[%(asctime)s] [PID %(process)d] [%(threadName)s] [%(name)s] '
        '[%(levelname)s] %(message)s'
    ),
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _get_credentials(client=None):
    if client is None:
        client = redis.Redis(host='redis')

    return {
        k: client.get(k).decode()
        for k in ('client_id', 'client_secret', 'refresh_token', 'access_token')
    }


def _count_business_days_between_dates(start, finish):
    count = 0
    current = start

    while current != finish:
        if current.weekday() < 5:
            count += 1
        current += datetime.timedelta(days=1)

    return count


def _add_months(start, num_months):
    num_years = (start.month + num_months - 1) // 12
    new_month = (start.month + num_months - 1) % 12 + 1
    # TODO: Handle day of month out of bounds for month
    return datetime.date(
        year=start.year + num_years,
        month=new_month,
        day=start.day,
    )


@cron('0 */6 * * *')  # Run every six hours
@dramatiq.actor
def refresh_monzo_credentials():
    redis_client = redis.Redis(host='redis')

    credentials = _get_credentials(redis_client)

    monzo_client = monzo.MonzoClient(**credentials)
    monzo_client.refresh_credentials()

    redis_client.set('access_token', monzo_client.access_token)
    redis_client.set('refresh_token', monzo_client.refresh_token)

    logger.info(
        'Refreshed Monzo credentials: client_id=%s',
        credentials['client_id'],
    )


@cron('0 19 * * 0,1,2,3,4')
@dramatiq.actor
def withdraw_from_pot():
    redis_client = redis.Redis(host='redis')
    credentials = _get_credentials(redis_client)

    account_id = redis_client.get('account_id').decode()
    pot_id = redis_client.get('pot_id').decode()
    amount = redis_client.get('amount').decode()

    monzo_client = monzo.MonzoClient(**credentials)
    monzo_client.withdraw_from_pot(account_id, pot_id, int(amount))

    logger.info('Withdrew money from pot.')


@cron('30 18 26 * *')
@dramatiq.actor
def deposit_to_pot():
    redis_client = redis.Redis(host='redis')

    today = datetime.today()
    month_ahead = _add_months(today, 1)
    num_days = _count_business_days_between_dates(today, month_ahead)

    account_id = redis_client.get('account_id').decode()
    pot_id = redis_client.get('pot_id').decode()
    day_amount = redis_client.get('amount').decode()

    month_amount = int(day_amount) * num_days

    credentials = _get_credentials(redis_client)

    monzo_client = monzo.MonzoClient(**credentials)
    monzo_client.deposit_to_pot(pot_id, account_id, month_amount)

    logger.info(f'Deposited {month_amount} to pot.')
