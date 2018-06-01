# Light userless Reddit api wrapper
# Developed by CantSayIHave
# 12/23/17


import uuid
import requests
import datetime


class Reddit:
    def __init__(self, **kwargs):
        self.client_id = kwargs.get('client_id', '')
        self.client_secret = kwargs.get('client_secret', '')
        self.token = kwargs.get('token', None)
        self.uuid = str(uuid.uuid4())[:30]
        self.token_expires = None

        if not self.token:
            self.get_token()

    def check_auth(self):
        header = {'Authorization': 'BEARER {}'.format(self.token)}

        r = requests.get('https://www.reddit.com/api/v1/me', headers=header)

        if r.status_code == 200:
            return True
        return False

    def get_token(self):
        data = {'grant_type': 'client_credentials',
                'device_id': self.uuid}

        r = requests.post('https://www.reddit.com/api/v1/access_token',
                          data=data,
                          auth=(self.client_id, self.client_secret))

        if r.status_code != 200:
            return False

        j = r.json()

