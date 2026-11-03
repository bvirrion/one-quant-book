from collections import OrderedDict, defaultdict


class LFU:
    def __init__(self, capacity):
        self.cap, self.lowest = capacity, 0
        self.value, self.freq = {}, {}
        self.by_freq = defaultdict(OrderedDict)    # frequency -> keys, oldest use first

    def _leave(self, key):            # an emptied group goes too, or by_freq grows for ever
        f = self.freq[key]
        del self.by_freq[f][key]
        if not self.by_freq[f]:
            del self.by_freq[f]
            if self.lowest == f:
                self.lowest = f + 1
        return f

    def _touch(self, key):
        f = self._leave(key)
        self.freq[key] = f + 1
        self.by_freq[f + 1][key] = True

    def get(self, key):
        if key not in self.value:
            return None
        self._touch(key)
        return self.value[key]

    def put(self, key, value):
        if self.cap == 0:
            return
        if key in self.value:
            self.value[key] = value
            self._touch(key)
            return
        if len(self.value) == self.cap:
            old = next(iter(self.by_freq[self.lowest]))
            self._leave(old)
            del self.value[old], self.freq[old]
        self.value[key], self.freq[key], self.lowest = value, 1, 1
        self.by_freq[1][key] = True
