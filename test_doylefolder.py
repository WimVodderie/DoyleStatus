import logging

from app import doylefolder
from app import doylefile


class mocked_cache:
    def __init__(self, logger):
        self.getCount = 0
        self.addCount = 0
        self.logger = logger

    def getDoyleFile(self, file):
        self.logger.info("getting from cache %s" % file)
        self.getCount = self.getCount + 1
        return None

    def addDoyleFile(self, file, doyleFile):
        self.logger.info("adding to cache %s" % file)
        self.addCount = self.addCount + 1


class mocked_db:
    def __init__(self,logger):
        self.logger=logger

    def loadFile(self, file):
        self.logger.info("getting from db %s" % file.filePath)
        return None

    def addFile(self, file):
        self.logger.info("adding to db %s" % file.filePath)

class TestDoyleFolder:
    def setup(self):
        LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
        self.d = doylefolder.DoyleFolder(doylefolder.DoyleFolderType.queueFolder, "./TestData/TestQueues/")
        logging.basicConfig(filename="./test_doylefolder.log", level=logging.DEBUG, format=LOG_FORMAT)
        self.logger = logging.getLogger()
        doylefile.DoyleFile.doyleFileDb = mocked_db(self.logger)

    def test_init(self):
        self.logger.info("test_init")
        assert len(self.d.items) == 0
        assert self.d.count == 0

    def test_update(self):
        self.logger.info("test_update")
        m = mocked_cache(self.logger)
        self.d.update(m)
        assert len(self.d.items) == 9
        assert self.d.count == 22
        assert m.getCount == 22
