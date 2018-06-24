
class DoyleFileCache:
    def __init__(self):
        # empty cache
        self.cache = {}
        self.resetUsedCount()

    def getDoyleFile(self, file):
        if file in self.cache:
            self.hitCount = self.hitCount + 1
            # increase used count for this item in the cache
            self.cache[file][0] = self.cache[file][0] + 1
            return self.cache[file][1]
        else:
            return None

    def addDoyleFile(self, file, doyleFile):
        self.cache[file] = [1, doyleFile]
        self.addCount = self.addCount + 1

    def resetUsedCount(self):
        self.addCount = 0
        self.removeCount = 0
        self.hitCount = 0
        for file in self.cache:
            self.cache[file][0] = 0

    def removeUnusedEntries(self):
        # build a list of all entries that have not been referenced
        toremove = []
        for file in self.cache:
            if self.cache[file][0] == 0:
                toremove.append((file,self.cache[file]))
        self.removeCount = self.removeCount + len(toremove)
        # remove them from the cache
        for (file,doyleFile) in toremove:
            del(self.cache[file])
        return toremove
