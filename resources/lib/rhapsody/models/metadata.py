class Metadata(object):
    url_base = ''
    cache_timeout = 60 * 60 * 2

    def __init__(self, api):
        self._api = api


class MetadataList(Metadata):
    class List(object):
        def __init__(self, data):
            self._data = data

    list_class = List

    def list(self, name, model=None):
        if model is None:
            model = self.list_class
        return self._api.get_list(model, self.url_base + '/' + name, limit=100, cache_timeout=self.cache_timeout)

    def top(self):
        return self.list('top')


class MetadataDetail(Metadata):
    class Detail(object):
        def __init__(self, data):
            self._data = data

    url_base = ''
    detail_class = Detail

    def detail(self, obj_id):
        return self._api.get_detail(self.detail_class, self.url_base, obj_id, cache_timeout=self.cache_timeout)