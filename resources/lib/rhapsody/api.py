import hashlib
import json
from datetime import timedelta

import requests

from rhapsody import cache
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
    TOKEN_CACHE_LIFETIME = timedelta(days=30).seconds
    DEFAULT_CACHE_TIMEOUT = timedelta(hours=2).seconds

    class NotAuthenticatedError(Exception):
        pass

    class AuthenticationError(Exception):
        pass

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

    def is_authenticated(self):
        try:
            return len(self.token.access_token) > 0
        except AttributeError:
            return False

    def login(self, username, password):
        if not self.is_authenticated() or self.token.username != username:
            data = {
                'username': username,
                'password': password,
                'grant_type': 'password'
            }
            try:
                response = requests.post(API.BASE_URL + 'oauth/token', data=data, auth=self._auth)
                self.token = Token(json.loads(response.text))
                self._cache.set('token', self.token, API.TOKEN_CACHE_LIFETIME)
            except KeyError:
                raise API.AuthenticationError
        elif self.token.is_expired():
            self.refresh_token()

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
        response = requests.post(API.BASE_URL + 'oauth/access_token', data=data, auth=self._auth)
        self.token.update_token(json.loads(response.text))
        self._cache.set('token', self.token, API.TOKEN_CACHE_LIFETIME)

    def post(self, url, data, headers=None):
        if headers is None:
            headers = dict()
        if self.is_authenticated():
            if self.token.is_expired():
                self.refresh_token()
            headers['Authorization'] = 'Bearer ' + self.token.access_token
        response = requests.post(API.BASE_URL + API.VERSION + '/' + url, data=data, headers=headers)
        #print 'RESPONSE: ' + str(response.text)
        return response.text

    def get_json(self, url, params, cache_timeout=DEFAULT_CACHE_TIMEOUT):
        cache_data = {
            'url': url,
            'params': params,
            'user': ''
        }
        headers = dict()
        if self.is_authenticated():
            if self.token.is_expired():
                self.refresh_token()
            params['catalog'] = self.token.catalog
            headers['Authorization'] = 'Bearer ' + self.token.access_token
            cache_data['user'] = self.token.username

        cache_key = hashlib.sha1(json.dumps(cache_data)).hexdigest()

        response_text = None
        if cache_timeout is not None:
            response_text = self._cache.get(cache_key, cache_timeout)

        if response_text is None:
            response = requests.get(API.BASE_URL + API.VERSION + '/' + url, params=params, headers=headers)
            #print response.request.url + ': ' + str(response.status_code) + ' - ' + response.text.encode('utf-8')
            response_text = response.text

            if cache_timeout is not None:
                self._cache.set(cache_key, response_text, cache_timeout)
        return response_text

    def get_detail(self, model, obj, obj_id, cache_timeout=None, params=None):
        if params is None:
            params = dict()
        params['apikey'] = self._key
        return model(json.loads(self.get_json(obj + '/' + obj_id, params, cache_timeout)))

    def get_list(self, model, obj, limit=None, offset=None, cache_timeout=None, params=None):
        if params is None:
            params = dict()
        params['apikey'] = self._key
        if limit is not None:
            params['limit'] = limit
            if offset is not None:
                params['offset'] = limit
        items = []
        for item in json.loads(self.get_json(obj, params, cache_timeout)):
            items.append(model(item))
        return items
