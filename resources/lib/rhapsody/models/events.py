from datetime import datetime
import json


class Events(object):
    def __init__(self, api):
        self._api = api

    def log_playstart(self, track_id, stream):
        started = datetime.utcnow()
        data = {
            'type': 'playbackStart',
            'client': 'py_rhapsody',
            'playback': {
                'id': track_id,
                'started': started.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'format': stream.format,
                'bitrate': stream.bitrate
            }
        }
        self._api.post('events', json.dumps(data), headers={'Content-Type': 'application/json'})
        return started

    def log_playstop(self, track_id, stream, started, duration=None):
        if duration is None:
            duration = (datetime.now() - started).seconds
        data = {
            'type': 'playbackStop',
            'duration': duration,
            'client': 'py_rhapsody',
            'playback': {
                'id': track_id,
                'started': started.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'format': stream.format,
                'bitrate': stream.bitrate
            }
        }
        self._api.post('events', json.dumps(data), headers={'Content-Type': 'application/json'})
