import json
import logging
import time
import uuid

import requests


logger = logging.getLogger(__name__)


class MonzoClient:

    def __init__(self, *, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        
        self.accounts = None
        self.pots = None

        self.refresh_credentials()

    @property
    def auth_header(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
        }

    @property
    def _credentials(self):
        return {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
        }

    @classmethod
    def from_file(cls, filepath, format='json'):
        if format == 'json':
            return cls._from_json_file(filepath)
        
        raise ValueError(f'Unsupported file format: \'{format}\'')

    @classmethod
    def _from_json_file(cls, filepath):

        with open(filepath) as f:
            data = json.load(f)

        client = cls(**data)

        with open(filepath, 'w') as f:
            json.dump(client._credentials, f)

        return client

    def refresh_credentials(self):

        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
        }

        response = requests.post(
            'https://api.monzo.com/oauth2/token',
            data=data,
        )
        response.raise_for_status()

        response_data = response.json()
        self.access_token = response_data['access_token']
        self.refresh_token = response_data['refresh_token']

        logger.info(
            'Successfully refreshed client credentials: client_id=%s',
            self.client_id,
        )

    def get_accounts(self):

        if self.accounts:
            return self.accounts

        response = requests.get(
            'https://api.monzo.com/accounts',
            headers=self.auth_header,
        )
        response.raise_for_status()

        self.accounts = response.json()['accounts']

        logger.info(
            'Fetched accounts from Monzo: num_accounts=%s', len(self.accounts),
        )

        return self.accounts

    def get_pots(self):

        if self.pots:
            return self.pots

        response = requests.get(
            'https://api.monzo.com/pots',
            headers=self.auth_header,
        )
        response.raise_for_status()

        self.pots = response.json()['pots']

        logger.info(
            'Fetched pots from Monzo: num_pots=%s', len(self.pots),
        )

        return self.pots

    def withdraw_from_pot(self, account_id, pot_id, amount):

        self._validate_transfer_endpoints(pot_id, account_id)

        dedupe_id = uuid.uuid4().hex

        logger.info(
            'Preparing to withdraw from pot: '
            'pot_id=%s, account_id=%s, amount=%s, dedupe_id=%s',
            pot_id, account_id, amount, dedupe_id,
        )

        data = {
            'destination_account_id': account_id,
            'amount': amount,
            'dedupe_id': dedupe_id,
        }
        response = self._put(
            f'https://api.monzo.com/pots/{pot_id}/withdraw',
            headers=self.auth_header, data=data,
        )

        return response.json()

    def deposit_to_pot(self, pot_id, account_id, amount):

        dedupe_id = uuid.uuid4().hex

        logger.info(
            'Preparing to deposit to pot: '
            'account_id=%s, pot_id=%s, amount=%s, dedupe_id=%s',
            account_id, pot_id, amount, dedupe_id,
        )

        data = {
            'source_account_id': account_id,
            'amount': amount,
            'dedupe_id': dedupe_id,
        }
        response = self._put(
            f'https://api.monzo.com/pots/{pot_id}/deposit',
            headers=self.auth_header, data=data,
        )

        return response.json()

    def _validate_transfer_endpoints(self, pot_id, account_id):

        if account_id not in {a['id'] for a in self.get_accounts()}:
            raise ValueError(f'Account not found: \'{account_id}\'')

        if pot_id not in {p['id'] for p in self.get_pots()}:
            raise ValueError(f'Pot not found: \'{pot_id}\'')

    def _put(self, url, headers, data, max_retries=3):

        interval = 0.1
        scale = 5

        for retry in range(max_retries):
            try:
                response = requests.put(url, headers=headers, data=data)
                response.raise_for_status()
            except requests.HTTPError as e:
                logger.warning(
                    'Error in HTTP response: code=%s, reason=%s, attempt=%s',
                    response.status_code.errno, response.reason, retry,
                )
                time.sleep(interval)
                interval *= scale
                continue

            return response

        response.raise_for_status()
