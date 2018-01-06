from app import doylefile

class DoyleFileCache:
    def __init__(self):
        # empty cache
        self.cache = {}
        self.resetUsedCount()

    def getDoyleFile(self, path, file):
        if file not in self.cache:
            doyleFile = doylefile.DoyleFile(path, file)
            doyleFile.load()
            self.cache[file] = [0, doyleFile]
            self.addCount = self.addCount + 1
        else:
            self.hitCount = self.hitCount + 1

        # increase used count for this item in the cache
        self.cache[file][0] = self.cache[file][0] + 1
        return self.cache[file][1]

    def resetUsedCount(self):
        self.addCount = 0
        self.removeCount = 0
        self.hitCount = 0
        for file in self.cache:
            self.cache[file][0] = 0

    def removeUnusedEntries(self):
        toremove = []
        for file in self.cache:
            if self.cache[file][0] == 0:
                self.cache[file][1].save()
                toremove.append(file)
                self.removeCount = self.removeCount + 1
        for file in toremove:
            del(self.cache[file])
