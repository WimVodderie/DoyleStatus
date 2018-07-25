
class _CacheElement:
    def __init__(self,doyleFile):
        self.usedCount=0
        self.doyleFile=doyleFile

    def hit(self):
        self.usedCount=self.usedCount+1

    def clear(self):
        self.usedCount=0


class DoyleFileCache:
    def __init__(self):
        # empty cache
        self.cache = {}
        self.resetUsedCount()

    def getDoyleFile(self, file):
        if file in self.cache:
            self.hitCount = self.hitCount + 1
            self.cache[file].hit()
            return self.cache[file].doyleFile
        else:
            return None

    def addDoyleFile(self, file, doyleFile):
        self.cache[file] = _CacheElement(doyleFile)
        self.addCount = self.addCount + 1

    def resetUsedCount(self):
        self.addCount = 0
        self.removeCount = 0
        self.hitCount = 0
        for file in self.cache:
            self.cache[file].clear()

    def removeUnusedEntries(self):
        # build a list of all entries that have not been referenced
        toremove = []
        for file in self.cache:
            if self.cache[file].usedCount == 0:
                toremove.append((file,self.cache[file].doyleFile))
        self.removeCount = self.removeCount + len(toremove)
        # remove them from the cache
        for (file,doyleFile) in toremove:
            del(self.cache[file])
        return toremove
