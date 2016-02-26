import datetime
import time


class Token(object):
    valid_until = None

    def __init__(self, data):
        self.username = data['username']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.access_token = data['access_token']
        self.expires_in = data['expires_in']
        self.token_type = data['token_type']
        self.catalog = data['catalog']
        self.guid = data['guid']
        self.refresh_token = data['refresh_token']

        if 'valid_until' in data:
            self.valid_until = data['valid_until']
        else:
            self._update_valid_until()

    def update_token(self, data):
        self.access_token = data['access_token']
        self.expires_in = data['expires_in']
        self.refresh_token = data['refresh_token']
        self._update_valid_until()

    def _update_valid_until(self):
        valid_until = datetime.datetime.now() + datetime.timedelta(seconds=int(self.expires_in))
        self.valid_until = time.mktime(valid_until.timetuple())

    def is_expired(self):
        if self.valid_until is None:
            return True
        valid_until = datetime.datetime.fromtimestamp(self.valid_until)
        return valid_until <= datetime.datetime.now() + datetime.timedelta(minutes=5)
