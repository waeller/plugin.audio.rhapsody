from metadata import *


class Image(MetadataDetail.Detail, object):
    def __init__(self, data):
        super(Image, self).__init__(data)
        self.width = data['width']
        self.height = data['height']
        self.url = data['url']