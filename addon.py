from multiprocessing.pool import ThreadPool
import os
import sys

from xbmcswift2 import Plugin, actions

plugin = Plugin()
sys.path.append(os.path.join(plugin.addon.getAddonInfo('path'), 'resources', 'lib'))

_ = plugin.get_string
cache = plugin.get_storage('data', TTL=0)

from helpers import Helpers

helpers = Helpers(plugin)
rhapsody = helpers.get_api()


@plugin.route('/')
def index():
    return [
        {'label': _(30200), 'path': plugin.url_for('library')},
        {'label': _(30201), 'path': plugin.url_for('search')},
        {'label': _(30202), 'path': plugin.url_for('discover')},
        {'label': _(30203), 'path': plugin.url_for('recent')},
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


@plugin.route('/discover')
def discover():
    return [
        {'label': _(30260), 'path': plugin.url_for('popular')},
        {'label': _(30261), 'path': plugin.url_for('genres')},
        {'label': _(30262), 'path': plugin.url_for('albums_new')},
        {'label': _(30263), 'path': plugin.url_for('albums_picks')},
        {'label': _(30264), 'path': plugin.url_for('playlists_featured')},
    ]


@plugin.route('/discover/popular')
def popular():
    return [
        {'label': _(30220), 'path': plugin.url_for('artists_top')},
        {'label': _(30221), 'path': plugin.url_for('albums_top')},
        {'label': _(30222), 'path': plugin.url_for('tracks_top')},
    ]


@plugin.route('/genres')
def genres():
    parent_genre_id = plugin.request.args.get('parent_genre_id', [None])[0]
    items = []
    if parent_genre_id is None:
        genres_list = rhapsody.genres.list()
    else:
        genres_list = rhapsody.genres.find(parent_genre_id).subgenres
    for genre in genres_list:
        items.append({'label': genre.name, 'path': plugin.url_for('genres_detail', genre_id=genre.id)})
    return items


@plugin.route('/genres/<genre_id>/detail')
def genres_detail(genre_id):
    return [
        {'label': _(30220), 'path': plugin.url_for('genres_artists_top', genre_id=genre_id)},
        {'label': _(30221), 'path': plugin.url_for('genres_albums_top', genre_id=genre_id)},
        {'label': _(30222), 'path': plugin.url_for('genres_tracks_top', genre_id=genre_id)},
        {'label': _(30262), 'path': plugin.url_for('genres_albums_new', genre_id=genre_id)},
        {'label': _(30265), 'path': plugin.url_for('genres', parent_genre_id=genre_id)},
    ]


@plugin.route('/genres/<genre_id>/artists/top')
def genres_artists_top(genre_id):
    items = []
    for artist in rhapsody.genres.top_artists(genre_id):
        items.append(helpers.get_artist_item(artist))
    return items


@plugin.route('/genres/<genre_id>/albums/top')
def genres_albums_top(genre_id):
    items = []
    for album in rhapsody.genres.top_albums(genre_id):
        items.append(helpers.get_album_item(album))
    return items


@plugin.route('/genres/<genre_id>/tracks/top')
def genres_tracks_top(genre_id):
    items = []
    for track in rhapsody.genres.top_tracks(genre_id):
        items.append(helpers.get_track_item(track))
    return items


@plugin.route('/genres/<genre_id>/albums/new')
def genres_albums_new(genre_id):
    items = []
    for album in rhapsody.genres.new_albums(genre_id):
        items.append(helpers.get_album_item(album))
    return items


@plugin.route('/search')
def search():
    query = plugin.keyboard(cache.get('last_search', ''), _(30240))
    if query is not None and len(query) > 0:
        cache['last_search'] = query
        items = []
        for result in rhapsody.search.fulltext(query):
            if result.type == 'artist':
                artist = result.data
                artist_item = helpers.get_artist_item(artist)
                artist_item['label'] = _(30241) + ': ' + artist_item['label']
                items.append(artist_item)
            if result.type == 'album':
                album = result.data
                album_item = helpers.get_album_item(album)
                album_item['label'] = _(30242) + ': ' + album_item['label']
                items.append(album_item)
            if result.type == 'track':
                track = result.data
                track_item = helpers.get_track_item(track)
                track_item['label'] = _(30243) + ': ' + track_item['label']
                items.append(track_item)
        if len(items) > 0:
            return items
        else:
            plugin.notify(_(30101).encode('utf-8'))


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
        items.append(helpers.get_artist_item(artist))
    return items


@plugin.route('/artists/recent')
def artists_recent():
    items = []
    for artist in rhapsody.library.recent_artists():
        items.append(helpers.get_artist_item(artist))
    return items


@plugin.route('/artists/library')
def artists_library():
    items = []
    for artist in rhapsody.library.artists():
        items.append(helpers.get_artist_item(artist, in_library=True))
    return items


@plugin.route('/artists/library/<artist_id>/albums')
def artists_library_albums(artist_id):
    items = []
    for album in rhapsody.library.artist_albums(artist_id):
        items.append(helpers.get_album_item(album, show_artist=False, in_library=True))
    return items


@plugin.route('/artists/library/<artist_id>/add')
def artists_library_add(artist_id):
    rhapsody.library.add_artist(artist_id)
    plugin.notify(_(30102))


@plugin.route('/artists/library/<artist_id>/remove')
def artists_library_remove(artist_id):
    rhapsody.library.remove_artist(artist_id)
    return plugin.finish(artists_library(), update_listing=True)


@plugin.route('/artists/<artist_id>/albums')
def artists_detail(artist_id):
    types = [0, 1]
    if not plugin.get_setting('hide_compilations', converter=bool):
        types.append(2)
    items = []
    for album in filter(lambda x: x.type.id in types, rhapsody.artists.albums(artist_id)):
        items.append(helpers.get_album_item(album, show_artist=False))
    return items


@plugin.route('/favorites/<track_id>/add')
def favorites_add(track_id):
    rhapsody.library.add_favorite(track_id)
    plugin.notify(_(30102))


@plugin.route('/favorites/<track_id>/remove')
def favorites_remove(track_id):
    rhapsody.library.remove_favorite(track_id)
    return plugin.finish(favorites_library(), update_listing=True)


@plugin.route('/favorites')
def favorites_library():
    items = []
    for track in rhapsody.library.favorites():
        items.append(helpers.get_track_item(track, in_favorites=True))
    return items


@plugin.route('/playlists/featured')
def playlists_featured():
    items = []
    for playlist in rhapsody.playlists.featured():
        items.append({'label': playlist.name, 'path': plugin.url_for('playlists_detail', playlist_id=playlist.id)})
    return items


@plugin.route('/playlists/library')
def playlists_library():
    items = [{'label': _(30250), 'path': plugin.url_for('playlists_library_add')}]
    for playlist in rhapsody.library.playlists():
        items.append({
            'label': playlist.name,
            'path': plugin.url_for('playlists_library_detail', playlist_id=playlist.id),
            'context_menu': [
                (
                    _(30251),
                    actions.update_view(plugin.url_for('playlists_library_rename', playlist_id=playlist.id))
                ),
                (
                    _(30252),
                    actions.update_view(plugin.url_for('playlists_library_remove', playlist_id=playlist.id))
                )
            ]
        })
    return items


@plugin.route('/playlists/library/add')
def playlists_library_add():
    name = plugin.keyboard('')
    if name is not None and len(name) > 0:
        rhapsody.library.add_playlist(name)
        helpers.refresh_playlists()
    return plugin.finish(playlists_library(), update_listing=True)


@plugin.route('/playlists/library/<playlist_id>/rename')
def playlists_library_rename(playlist_id):
    name = plugin.keyboard('')
    if name is not None and len(name) > 0:
        rhapsody.library.rename_playlist(playlist_id, name)
        helpers.refresh_playlists()
    helpers.refresh_playlists()
    return plugin.finish(playlists_library(), update_listing=True)


@plugin.route('/playlists/library/<playlist_id>/remove')
def playlists_library_remove(playlist_id):
    rhapsody.library.remove_playlist(playlist_id)
    helpers.refresh_playlists()
    return plugin.finish(playlists_library(), update_listing=True)


@plugin.route('/playlists/library/<playlist_id>/detail')
def playlists_library_detail(playlist_id):
    playlist = rhapsody.library.playlist(playlist_id)
    items = []
    for track in playlist.tracks:
        items.append(helpers.get_track_item(track, in_playlists=True, playlist_id=playlist_id))
    return items


@plugin.route('/playlists/library/<playlist_id>/add/<track_id>')
def playlists_library_add_track(playlist_id, track_id):
    rhapsody.library.add_track_to_playlist(track_id, playlist_id)
    plugin.notify(_(30102))


@plugin.route('/playlists/library/<playlist_id>/remove/<track_id>')
def playlists_library_remove_track(playlist_id, track_id):
    rhapsody.library.remove_track_from_playlist(track_id, playlist_id)
    return plugin.finish(playlists_library_detail(playlist_id), update_listing=True)


@plugin.route('/playlists/<playlist_id>')
def playlists_detail(playlist_id):
    playlist = rhapsody.playlists.detail(playlist_id)
    items = []
    for track in playlist.tracks:
        items.append(helpers.get_track_item(track))
    return items


@plugin.route('/albums/top')
def albums_top():
    items = []
    for album in rhapsody.albums.top():
        items.append(helpers.get_album_item(album))
    return items


@plugin.route('/albums/new')
def albums_new():
    items = []
    for album in rhapsody.albums.new():
        items.append(helpers.get_album_item(album))
    return items


@plugin.route('/albums/picks')
def albums_picks():
    items = []
    for album in rhapsody.albums.picks():
        items.append(helpers.get_album_item(album))
    return items


@plugin.route('/albums/library')
def albums_library():
    items = []
    for album in rhapsody.library.albums():
        items.append(helpers.get_album_item(album, in_library=True))
    return items


@plugin.route('/albums/library/<album_id>/tracks')
def albums_library_tracks(album_id):
    items = []
    for track in rhapsody.library.album_tracks(album_id):
        track_item = helpers.get_track_item(track, show_artist=False, in_library=True)
        items.append(track_item)
    plugin.add_to_playlist(items, playlist='music')
    return items


@plugin.route('/albums/library/<album_id>/add')
def albums_library_add(album_id):
    rhapsody.library.add_album(album_id)
    plugin.notify(_(30102))


@plugin.route('/albums/library/<album_id>/remove')
def albums_library_remove(album_id):
    rhapsody.library.remove_album(album_id)
    return plugin.finish(albums_library(), update_listing=True)


@plugin.route('/albums/<album_id>')
def albums_detail(album_id):
    album = rhapsody.albums.detail(album_id)
    items = []
    for track in album.tracks:
        items.append(helpers.get_track_item(track, album, show_artist=False))
    return items


@plugin.route('/tracks/top')
def tracks_top():
    items = []
    for track in rhapsody.tracks.top():
        track_item = helpers.get_track_item(track)
        items.append(track_item)
    plugin.add_to_playlist(items, playlist='music')
    return items


@plugin.route('/tracks/recent')
def tracks_recent():
    items = []
    for track in rhapsody.library.recent_tracks():
        track_item = helpers.get_track_item(track)
        items.append(track_item)
    plugin.add_to_playlist(items, playlist='music')
    return items


@plugin.route('/tracks/library')
def tracks_library():
    items = []
    for track in rhapsody.library.tracks():
        track_item = helpers.get_track_item(track, in_library=True)
        items.append(track_item)
    plugin.add_to_playlist(items, playlist='music')
    return items


@plugin.route('/tracks/library/<track_id>/add')
def tracks_library_add(track_id):
    rhapsody.library.add_track(track_id)
    plugin.notify(_(30102))


@plugin.route('/tracks/library/<track_id>/remove')
def tracks_library_remove(track_id):
    rhapsody.library.remove_track(track_id)
    return plugin.finish(tracks_library(), update_listing=True)


@plugin.route('/play/<track_id>')
def play(track_id):
    album_id = plugin.request.args.get('album_id', [False])[0]
    duration = plugin.request.args.get('duration', [False])[0]
    thumbnail_missing = plugin.request.args.get('thumbnail_missing', [False])[0]

    item = dict()
    pool = ThreadPool(processes=2)

    stream_result = pool.apply_async(lambda: rhapsody.streams.detail(track_id))

    if thumbnail_missing:
        album_result = pool.apply_async(lambda: rhapsody.albums.detail(album_id))
        album = album_result.get()
        item['thumbnail'] = album.images[0].url

    stream = stream_result.get()
    item['path'] = stream.url
    plugin.set_resolved_url(item)

    started = rhapsody.events.log_playstart(track_id, stream)
    rhapsody.events.log_playstop(track_id, stream, started, duration)

    pool.close()
    pool.join()


if __name__ == '__main__':
    plugin.run()