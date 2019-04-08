import logging

from app import doylefolder
from app import doylefile


class mocked_cache:
    def __init__(self):
        self.getCount = 0
        self.addCount = 0

    def getDoyleFile(self, file):
        self.getCount = self.getCount + 1
        return None

    def addDoyleFile(self, file, doyleFile):
        self.addCount = self.addCount + 1


class mocked_db:
    def __init__(self):
        self.loadCount = 0
        self.addCount = 0

    def loadFile(self, file):
        self.loadCount = self.loadCount + 1
        return None

    def addFile(self, file):
        self.addCount = self.addCount + 1


class TestDoyleFolder:
    def setup(self):
        self.d = doylefolder.DoyleFolder(doylefolder.DoyleFolderType.queueFolder, "./TestData/TestQueues/")
        doylefile.DoyleFile.doyleFileDb = mocked_db()

    def test_init(self):
        assert len(self.d.items) == 0
        assert self.d.count == 0

    def test_update(self):
        m = mocked_cache()
        self.d.update(m)
        assert len(self.d.items) == 9
        assert self.d.count == 22
        assert m.getCount == 22
