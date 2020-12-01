import os
import datetime
import tempfile

from app import doylefiledb

#testDbPath="./TestData/TestDb"
testDbPath="/tmp"
testDbBackupPath="/tmp"

class TestDoyleQueueDb:
    def setup(self):
        self.dbPath = tempfile.TemporaryDirectory()
        self.d = doylefiledb.DoyleFileDb(self.dbPath.name,self.dbPath.name)

    def teardown(self):
        self.d.quit()
        self.dbPath.cleanup()

    def test_init(self):
        pass
