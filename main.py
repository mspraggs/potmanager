"""The main pot management app.

Usage:
  main.py [--dry-run] <amount>
  main.py (-h | --help)
  main.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --dry-run     Don't execute transfers.

"""
import datetime
import sys

from docopt import DocoptExit
from docopt import docopt

import monzo
import settings


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

    today = datetime.date.today()

    if today.weekday() >= 5:
        sys.exit()

    client = monzo.MonzoClient.from_file(
        settings.MONZO_CREDENTIALS_FILE, 'json',
    )

    accounts = client.get_accounts()
    pots = client.get_pots()

    if not arguments['--dry-run']:
        client.withdraw_from_pot(
            settings.ACCOUNT_ID,
            settings.POT_ID,
            arguments['<amount>'],
        )
