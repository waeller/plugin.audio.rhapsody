from metadata import *


class Detail(object):
    def __init__(self, data):
        self.url = data['url']
        self.bitrate = data['bitrate']
        self.format = data['format']


class Streams(MetadataDetail):
    url_base = 'play'
    detail_class = Detail
    cache_timeout = 600