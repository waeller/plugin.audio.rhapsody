import os
import sys

from xbmcswift2 import Plugin

plugin = Plugin()
sys.path.append(os.path.join(plugin.addon.getAddonInfo('path'), 'resources', 'lib'))

_ = plugin.get_string

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


api_key = plugin.get_setting('api_key', converter=unicode)
api_secret = plugin.get_setting('api_secret', converter=unicode)
rhapsody = API(api_key, api_secret, cache_class=Cache)

try:
    username = plugin.get_setting('username', converter=unicode)
    password = plugin.get_setting('password', converter=unicode)
    rhapsody.login(username, password)
except rhapsody.AuthenticationError:
    plugin.notify(_(30100).encode('utf-8'))
    plugin.open_settings()
    exit()


def get_album_item(album, show_artist=True):
    if show_artist:
        label = album.artist.name + ' - ' + album.name + ' (' + str(album.get_release_date().year) + ')'
    else:
        label = album.name + ' (' + str(album.get_release_date().year) + ')'
    return {
        'label': label,
        'path': plugin.url_for('albums_detail', album_id=album.id),
        'thumbnail': album.images[0].url
    }


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
        {'label': _(30200), 'path': plugin.url_for('library')},
        {'label': _(30201), 'path': plugin.url_for('search')},
        {'label': _(30202), 'path': plugin.url_for('toplist')},
        {'label': _(30203), 'path': plugin.url_for('albums_new')},
        {'label': _(30204), 'path': plugin.url_for('albums_picks')},
        {'label': _(30205), 'path': plugin.url_for('playlists_featured')},
        {'label': _(30206), 'path': plugin.url_for('recent')},
    ]


@plugin.route('/library')
def library():
    return [
        {'label': _(30210), 'path': plugin.url_for('artists_library')},
        {'label': _(30211), 'path': plugin.url_for('albums_library')},
        {'label': _(30212), 'path': plugin.url_for('tracks_library')},
        {'label': _(30213), 'path': plugin.url_for('favorites_library')},
        {'label': _(30214), 'path': plugin.url_for('playlists_library')},
    ]


@plugin.route('/search')
def search():
    query = plugin.keyboard('', _(30240))
    if query is not None:
        items = []
        for result in rhapsody.search.fulltext(query):
            if result.type == 'artist':
                artist = result.data
                items.append({
                    'label': _(30241) + ': ' + artist.name,
                    'path': plugin.url_for('artists_detail', artist_id=artist.id)
                })
            if result.type == 'album':
                album = result.data
                album_item = get_album_item(album)
                album_item['label'] = _(30242) + ': ' + album.artist.name + ' - ' + album.name
                items.append(album_item)
            if result.type == 'track':
                track = result.data
                track_item = get_track_item(track)
                track_item['label'] = _(30243) + ': ' + track.artist.name + ' - ' + track.name
                items.append(track_item)
        if len(items) > 0:
            return items
        else:
            plugin.notify(_(30101).encode('utf-8'))


@plugin.route('/top')
def toplist():
    return [
        {'label': _(30220), 'path': plugin.url_for('artists_top')},
        {'label': _(30221), 'path': plugin.url_for('albums_top')},
        {'label': _(30222), 'path': plugin.url_for('tracks_top')},
    ]


@plugin.route('/recent')
def recent():
    return [
        {'label': _(30230), 'path': plugin.url_for('artists_recent')},
        {'label': _(30231), 'path': plugin.url_for('tracks_recent')},
    ]


@plugin.route('/artists/top')
def artists_top():
    items = []
    for artist in rhapsody.artists.top():
        items.append({'label': artist.name, 'path': plugin.url_for('artists_detail', artist_id=artist.id)})
    return items


@plugin.route('/artists/recent')
def artists_recent():
    items = []
    for artist in rhapsody.library.recent_artists():
        items.append({'label': artist.name, 'path': plugin.url_for('artists_detail', artist_id=artist.id)})
    return items


@plugin.route('/artists/library')
def artists_library():
    items = []
    for artist in rhapsody.library.artists():
        items.append({'label': artist.name, 'path': plugin.url_for('artists_detail', artist_id=artist.id)})
    return items


@plugin.route('/artists/<artist_id>/albums')
def artists_detail(artist_id):
    types = [0, 1]
    if not plugin.get_setting('hide_compilations', converter=bool):
        types.append(2)
    items = []
    for album in filter(lambda x: x.type.id in types, rhapsody.artists.albums(artist_id)):
        items.append(get_album_item(album, show_artist=False))
    return items


@plugin.route('/favorites')
def favorites_library():
    items = []
    for track in rhapsody.library.favorites():
        items.append(get_track_item(track))
    return items


@plugin.route('/playlists/featured')
def playlists_featured():
    items = []
    for playlist in rhapsody.playlists.featured():
        items.append({'label': playlist.name, 'path': plugin.url_for('playlists_detail', playlist_id=playlist.id)})
    return items


@plugin.route('/playlists/library')
def playlists_library():
    items = []
    for playlist in rhapsody.library.playlists():
        items.append({
            'label': playlist.name,
            'path': plugin.url_for('playlists_library_detail', playlist_id=playlist.id)
        })
    return items


@plugin.route('/playlists/library/<playlist_id>')
def playlists_library_detail(playlist_id):
    playlist = rhapsody.library.playlist(playlist_id)
    items = []
    for track in playlist.tracks:
        items.append(get_track_item(track))
    return items


@plugin.route('/playlists/<playlist_id>')
def playlists_detail(playlist_id):
    playlist = rhapsody.playlists.detail(playlist_id)
    items = []
    for track in playlist.tracks:
        items.append(get_track_item(track))
    return items


@plugin.route('/albums/top')
def albums_top():
    items = []
    for album in rhapsody.albums.top():
        items.append(get_album_item(album))
    return items


@plugin.route('/albums/new')
def albums_new():
    items = []
    for album in rhapsody.albums.new():
        items.append(get_album_item(album))
    return items


@plugin.route('/albums/picks')
def albums_picks():
    items = []
    for album in rhapsody.albums.picks():
        items.append(get_album_item(album))
    return items


@plugin.route('/albums/library')
def albums_library():
    items = []
    for album in rhapsody.library.albums():
        items.append(get_album_item(album))
    return items


@plugin.route('/albums/<album_id>')
def albums_detail(album_id):
    album = rhapsody.albums.detail(album_id)
    items = []
    for track in album.tracks:
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


@plugin.route('/tracks/recent')
def tracks_recent():
    items = []
    for track in rhapsody.library.recent_tracks():
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


@plugin.route('/play/<track_id>')
def play(track_id):
    add_metadata = plugin.request.args.get('add_metadata', [False])[0]
    stream = rhapsody.streams.detail(track_id)
    track = rhapsody.tracks.detail(track_id)
    album = None
    if add_metadata == 'True':
        album = rhapsody.albums.detail(track.album.id)
    item = get_track_item(track, album)
    item['path'] = stream.url
    started = rhapsody.events.log_playstart(track_id, stream)
    rhapsody.events.log_playstop(track_id, stream, started, track.duration)
    plugin.set_resolved_url(item)


if __name__ == '__main__':
    plugin.run()
