import hashlib
import json

import requests
from requests.exceptions import ConnectionError

from rhapsody import cache, exceptions
from rhapsody.account import Account
from rhapsody.models.albums import Albums
from rhapsody.models.artists import Artists
from rhapsody.models.events import Events
from rhapsody.models.genres import Genres
from rhapsody.models.library import Library
from rhapsody.models.playlists import Playlists
from rhapsody.models.search import Search
from rhapsody.models.streams import Streams
from rhapsody.models.tracks import Tracks
from rhapsody.token import Token


class API:
    BASE_URL = 'https://api.rhapsody.com/'
    VERSION = 'v1'
    TOKEN_CACHE_LIFETIME = 60 * 60 * 24 * 7   # 7 days
    DEFAULT_CACHE_TIMEOUT = 60 * 60 * 2       # 2 hours
    MAX_RETRIES = 3
    DEBUG = False

    instance = None
    token = Token

    def __init__(self, key, secret, cache_instance=cache.Dummy()):
        API.instance = self

        self._cache = cache_instance
        self._auth = (key, secret)
        self._key = key
        self._secret = secret

        self.artists = Artists(self)
        self.albums = Albums(self)
        self.events = Events(self)
        self.genres = Genres(self)
        self.library = Library(self)
        self.playlists = Playlists(self)
        self.search = Search(self)
        self.streams = Streams(self)
        self.tracks = Tracks(self)

        self.token = self._cache.get('token', API.TOKEN_CACHE_LIFETIME)
        self.account = self._cache.get('account', API.TOKEN_CACHE_LIFETIME)

    def is_authenticated(self):
        try:
            return len(self.token.access_token) > 0
        except AttributeError:
            return False

    def login(self, username, password, reuse_token=True):
        if not self.is_authenticated() or self.token.username != username or not reuse_token:
            data = {
                'username': username,
                'password': password,
                'grant_type': 'password'
            }
            try:
                response = requests.post(API.BASE_URL + 'oauth/token', data=data, auth=self._auth)
                self.token = Token(json.loads(response.text))
                self.account = None
                self._cache.set('token', self.token, API.TOKEN_CACHE_LIFETIME)
            except KeyError:
                raise exceptions.AuthenticationError
            except ConnectionError:
                raise exceptions.RequestError
            self._log_response(response)
        elif self.token.is_expired():
            try:
                self.refresh_token()
                self.account = None
            except KeyError:
                self.login(username, password, reuse_token=False)
        if self.account is None:
            self.account = self.get_detail(Account, 'me', 'account')
            self._cache.set('account', self.account, API.TOKEN_CACHE_LIFETIME)

    def logout(self):
        self.token = None

    def refresh_token(self):
        data = {
            'client_id': self._key,
            'client_secret': self._secret,
            'response_type': 'code',
            'grant_type': 'refresh_token',
            'refresh_token': self.token.refresh_token
        }
        try:
            response = requests.post(API.BASE_URL + 'oauth/access_token', data=data, auth=self._auth)
        except ConnectionError:
            raise exceptions.RequestError
        self._log_response(response)
        self.token.update_token(json.loads(response.text))
        self._cache.set('token', self.token, API.TOKEN_CACHE_LIFETIME)

    def _get_headers(self, headers=None):
        if headers is None:
            headers = dict()
        if self.is_authenticated():
            if self.token.is_expired():
                self.refresh_token()
            headers['Authorization'] = 'Bearer ' + self.token.access_token
        return headers

    def _log_response(self, response):
        if self.DEBUG:
            print {
                'request': {
                    'url': response.request.url,
                },
                'response': {
                    'status': response.status_code,
                    'text': response.text
                }
            }

    def get(self, url, params, headers=None, retry=0):
        headers = self._get_headers(headers)
        try:
            response = requests.get(API.BASE_URL + API.VERSION + '/' + url, params=params, headers=headers)
        except ConnectionError:
            if retry < self.MAX_RETRIES:
                return self.get(url, params, headers, retry + 1)
            else:
                raise exceptions.RequestError
        if response.status_code == 404:
            raise exceptions.ResourceNotFoundError
        self._log_response(response)
        return response.text

    def post(self, url, data, headers=None, retry=0):
        headers = self._get_headers(headers)
        try:
            response = requests.post(API.BASE_URL + API.VERSION + '/' + url, data=data, headers=headers)
        except ConnectionError:
            if retry < self.MAX_RETRIES:
                return self.post(url, data, headers, retry + 1)
            else:
                raise exceptions.RequestError
        self._log_response(response)
        return response.text

    def put(self, url, data, headers=None, retry=0):
        headers = self._get_headers(headers)
        try:
            response = requests.put(API.BASE_URL + API.VERSION + '/' + url, data=data, headers=headers)
        except ConnectionError:
            if retry < self.MAX_RETRIES:
                return self.put(url, data, headers, retry + 1)
            else:
                raise exceptions.RequestError
        self._log_response(response)
        return response.text

    def delete(self, url, headers=None, retry=0):
        headers = self._get_headers(headers)
        try:
            response = requests.delete(API.BASE_URL + API.VERSION + '/' + url, headers=headers)
        except ConnectionError:
            if retry < self.MAX_RETRIES:
                return self.delete(url, headers, retry + 1)
            else:
                raise exceptions.RequestError
        self._log_response(response)
        return response.text

    def get_json(self, url, params, cache_timeout=DEFAULT_CACHE_TIMEOUT, retry=0):
        cache_data = {
            'url': url,
            'params': params,
            'user': ''
        }

        if self.is_authenticated():
            if self.token.is_expired():
                self.refresh_token()
            params['catalog'] = self.token.catalog
            cache_data['user'] = self.token.username

        cache_key = hashlib.sha1(json.dumps(cache_data)).hexdigest()

        response_text = None
        if cache_timeout is not None and not self.DEBUG and retry == 0:
            response_text = self._cache.get(cache_key, cache_timeout)

        if response_text is None:
            response_text = self.get(url, params=params, headers=self._get_headers())
            if cache_timeout is not None:
                self._cache.set(cache_key, response_text, cache_timeout)

        try:
            return json.loads(response_text)
        except ValueError:
            if retry < self.MAX_RETRIES:
                return self.get_json(url, params, cache_timeout, retry + 1)
            else:
                raise exceptions.ResponseError

    def get_detail(self, model, obj, obj_id, cache_timeout=None, params=None):
        if params is None:
            params = dict()
        params['apikey'] = self._key
        return model(self.get_json(obj + '/' + obj_id, params, cache_timeout))

    def get_list(self, model, obj, limit=None, offset=None, cache_timeout=None, params=None):
        if params is None:
            params = dict()
        params['apikey'] = self._key
        if limit is not None:
            params['limit'] = limit
            if offset is not None:
                params['offset'] = limit
        items = []
        for item in self.get_json(obj, params, cache_timeout):
            items.append(model(item))
        return items
