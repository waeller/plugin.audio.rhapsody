class Base(object):
    def get(self, key, timeout):
        pass

    def set(self, key, value, timeout):
        pass


class Dummy(Base):
    def get(self, key, timeout):
        return None

    def set(self, key, value, timeout):
        return True