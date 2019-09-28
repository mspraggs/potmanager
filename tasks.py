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
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


def _get_credentials(client=None):
    if client is None:
        client = redis.Redis(host='redis')

    return {
        k: client.get(k).decode()
        for k in ('client_id', 'client_secret', 'refresh_token', 'access_token')
    }


@cron('* */6 * * *')  # Run every six hours
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


@cron('0 19 * * 1,2,3,4,5')
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
