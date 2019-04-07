import logging

from app import doylefolder


class mocked_cache:
    def __init__(self, logger):
        self.getCount = 0
        self.logger = logger

    def getDoyleFile(self, file):
        self.logger.info("getting %s" % file)
        self.getCount = self.getCount + 1


class TestDoyleFolder:
    def setup(self):
        LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
        self.d = doylefolder.DoyleFolder(doylefolder.DoyleFolderType.queueFolder, "./TestData/TestQueues/")
        logging.basicConfig(filename="./test_doylefolder.log", level=logging.DEBUG, format=LOG_FORMAT)
        self.logger = logging.getLogger()

    def test_init(self):
        self.logger.info("test_init")
        assert len(self.d.items) == 0
        assert self.d.count == 0

    def test_update(self):
        self.logger.info("test_update")
        m = mocked_cache(self.logger)
        self.d.update(m)
        assert len(self.d.items) == 0
        assert self.d.count == 0
        #assert m.getCount == 10
