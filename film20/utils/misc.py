class ListWrapper(object):
    def __init__(self, list, wrap_func=None):
        self.list = list
        self.wrap_func = wrap_func

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.list[i], self.wrap_func)
        if isinstance(i, (int, long)):
            return self.wrapper(self.list[i])

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        for i in self.list:
            yield self.wrapper(i)

    def wrapper(self, item):
        if self.wrap_func:
            return self.wrap_func(item)
        raise NotImplementedError()


