class database:
    def __init__(self, name, size, lastUpdate, sizeInBytes):
        self.name = name
        self.size = size
        self.lastUpdate = lastUpdate
        self.sizeInBytes = sizeInBytes

    def toString(self):
        return "| Name: {0:25}| Size:{1:11}| Last Update: {2:12} |".format(self.name, self.size, self.lastUpdate)

