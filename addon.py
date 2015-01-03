import os
import sys

from xbmcswift2 import Plugin


plugin = Plugin()
sys.path.append(os.path.join(plugin.addon.getAddonInfo('path'), 'resources', 'lib'))

from rhapsody import cache
from rhapsody.api import API


class Cache(cache.Base):
    def __init__(self):
        self.storages = {}

    def get_storage(self, timeout):
        timeout = int(timeout / 60)
        if timeout not in self.storages:
            self.storages[timeout] = plugin.get_storage('data.{0:d}'.format(timeout), TTL=timeout)
        return self.storages[timeout]

    def get(self, key, timeout):
        storage = self.get_storage(timeout)
        return storage.get(key)

    def set(self, key, value, timeout):
        storage = self.get_storage(timeout)
        storage[key] = value


rhapsody = API(plugin.get_setting('api_key'), plugin.get_setting('api_secret'), cache_class=Cache)

try:
    rhapsody.login(plugin.get_setting('username'), plugin.get_setting('password'))
except rhapsody.AuthenticationError:
    plugin.notify('Login failed. Check your credentials.')
    plugin.open_settings()
    exit()


def get_track_item(track, album=None):
    item = {
        'label': track.name,
        'is_playable': True,
        'info': {
            'title': track.name,
            'artist': track.artist.name,
            'album': track.album.name,
            'duration': track.duration
        }
    }
    if album is None:
        needs_metadata = True
    else:
        needs_metadata = False
        item['thumbnail'] = album.images[0].url
        item['info']['tracknumber'] = [i for i, j in enumerate(album.tracks) if j.id == track.id][0] + 1
    item['path'] = plugin.url_for('play', track_id=track.id, add_metadata=needs_metadata)
    return item


@plugin.route('/')
def index():
    return [
        {'label': 'Library', 'path': plugin.url_for('library')},
        {'label': 'Search', 'path': plugin.url_for('search')},
        {'label': 'Top', 'path': plugin.url_for('toplist')},
    ]


@plugin.route('/library')
def library():
    return [
        {'label': 'Artists', 'path': plugin.url_for('artists_library')},
        {'label': 'Albums', 'path': plugin.url_for('albums_library')},
        {'label': 'Tracks', 'path': plugin.url_for('tracks_library')},
    ]


@plugin.route('/search')
def search():
    query = plugin.keyboard('', 'Search')
    if query is not None:
        items = []
        for result in rhapsody.search.fulltext(query):
            if result.type == 'artist':
                artist = result.data
                items.append({
                    'label': 'Artist' + ': ' + artist.name,
                    'path': plugin.url_for('artists_detail', artist_id=artist.id)
                })
            if result.type == 'album':
                album = result.data
                items.append({
                    'label': 'Album' + ': ' + album.artist.name + ' - ' + album.name,
                    'path': plugin.url_for('albums_detail', album_id=album.id),
                    'thumbnail': album.images[0].url
                })
            if result.type == 'track':
                track = result.data
                track_item = get_track_item(track)
                track_item['label'] = 'Track' + ': ' + track.artist.name + ' - ' + track.name
                items.append(track_item)
        if len(items) > 0:
            return items
        else:
            plugin.notify('No results found')


@plugin.route('/top')
def toplist():
    return [
        {'label': 'Artists', 'path': plugin.url_for('artists_top')},
        {'label': 'Albums', 'path': plugin.url_for('albums_top')},
        {'label': 'Tracks', 'path': plugin.url_for('tracks_top')},
    ]


@plugin.route('/artists/top')
def artists_top():
    items = []
    for artist in rhapsody.artists.top():
        items.append({'label': artist.name, 'path': plugin.url_for('artists_detail', artist_id=artist.id)})
    return items


@plugin.route('/artists/library')
def artists_library():
    items = []
    for artist in rhapsody.library.artists():
        items.append({'label': artist.name, 'path': plugin.url_for('artists_detail', artist_id=artist.id)})
    return items


@plugin.route('/artists/<artist_id>')
def artists_detail(artist_id):
    items = []
    for album in rhapsody.artists.albums(artist_id):
        items.append({
            'label': album.name,
            'path': plugin.url_for('albums_detail', album_id=album.id),
            'thumbnail': album.images[0].url
        })
    return items


@plugin.route('/albums/top')
def albums_top():
    items = []
    for album in rhapsody.albums.top():
        items.append({
            'label': album.artist.name + ' - ' + album.name,
            'path': plugin.url_for('albums_detail', album_id=album.id),
            'thumbnail': album.images[0].url
        })
    return items


@plugin.route('/albums/library')
def albums_library():
    items = []
    for album in rhapsody.library.albums():
        items.append({
            'label': album.artist.name + ' - ' + album.name,
            'path': plugin.url_for('albums_detail', album_id=album.id),
            'thumbnail': album.images[0].url
        })
    return items


@plugin.route('/albums/<album_id>')
def albums_detail(album_id):
    album = rhapsody.albums.detail(album_id)
    items = []
    for track in rhapsody.albums.tracks(album_id):
        items.append(get_track_item(track, album))
    return items


@plugin.route('/tracks/top')
def tracks_top():
    items = []
    for track in rhapsody.tracks.top():
        track_item = get_track_item(track)
        track_item['label'] = track.artist.name + ' - ' + track.name
        items.append(track_item)
    plugin.add_to_playlist(items, playlist='music')
    return items


@plugin.route('/tracks/library')
def tracks_library():
    items = []
    for track in rhapsody.library.tracks():
        track_item = get_track_item(track)
        track_item['label'] = track.artist.name + ' - ' + track.name
        items.append(track_item)
    plugin.add_to_playlist(items, playlist='music')
    return items


@plugin.route('/play/<track_id>/<add_metadata>')
def play(track_id, add_metadata):
    stream = rhapsody.streams.detail(track_id)
    if add_metadata == 'True':
        track = rhapsody.tracks.detail(track_id)
        album = rhapsody.albums.detail(track.album.id)
        item = get_track_item(track, album)
    else:
        item = dict()
    item['path'] = stream.url
    plugin.set_resolved_url(item)


if __name__ == '__main__':
    plugin.run()
