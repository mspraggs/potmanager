"""The main pot management app.

Usage:
  main.py [--dry-run] [--force] <amount>
  main.py (-h | --help)
  main.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --dry-run     Don't execute transfers.
  --force       Override scheduling and force transfer.

"""
import datetime
import logging
import sys

from docopt import DocoptExit
from docopt import docopt

import monzo
import settings


logging.basicConfig(
    format=(
        '[%(asctime)s] [PID %(process)d] [%(threadName)s] [%(name)s] '
        '[%(levelname)s] %(message)s'
    ),
    level=logging.INFO,
)


if __name__ == '__main__':
    try:
        arguments = docopt(__doc__, help=True, version='Pot Manager 0.0-alpha')
        arguments['<amount>'] = int(arguments['<amount>'])
    except DocoptExit as e:
        print(e)
        sys.exit()
    except ValueError as e:
        print('Amount must be an integer.')
        sys.exit()

    client = monzo.MonzoClient.from_file(
        settings.MONZO_CREDENTIALS_FILE, 'json',
    )

    today = datetime.date.today()

    if not arguments['--force'] and today.weekday() >= 5:
        sys.exit()

    accounts = client.get_accounts()
    pots = client.get_pots()

    if not arguments['--dry-run']:
        client.withdraw_from_pot(
            settings.ACCOUNT_ID,
            settings.POT_ID,
            arguments['<amount>'],
        )
