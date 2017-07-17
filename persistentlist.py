class PersistentList:
    def __init__(self, filename, mapf=None):
        self.filename = filename
        self.mapf = mapf

    def __iter__(self):
        try:
            with self.open() as f:
                return iter(self.mapped(l.strip()) for l in f.readlines())
        except FileNotFoundError:
            return iter([])

    def mapped(self, item):
        if self.mapf:
            return self.mapf(str(item))
        else:
            return str(item)

    def extend(self, items):
        with self.open('a') as f:
            for item in items:
                f.write(self.mapped(item) + '\n')

    def set(self, items):
        with self.open('w') as f:
            for item in items:
                f.write(self.mapped(item) + '\n')

    def remove_all(self, items):
        content = list(self)
        for item in items:
            item = self.mapped(item)
            if item in content:
                content.remove(item)
        self.set(content)

    def open(self, mode='r'):
        return open(self.filename, mode)

    def clear(self):
        self.set([])

    def append(self, item):
        self.extend([item])

    def remove(self, item):
        self.remove_all([item])

    def __contains__(self, item):
        return self.mapped(item) in list(self)

    def __str__(self):
        return 'PersistentList(%s)' % self.filename

    def __repr__(self):
        return str(self) + str(list(self))
