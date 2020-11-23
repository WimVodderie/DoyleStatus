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
        start_date=datetime.datetime(year=2000,month=1,day=1)
        end_date=datetime.datetime(year=2000,month=12,day=31)
        assert len(self.d.getQueuedCounts(start_date,end_date)) == 0

    def test_add(self):
        d=datetime.datetime(year=2000,month=1,day=2)
        c=10
        self.d.addQueuedCount(d,c)

        # now there should be one entry
        start_date=datetime.datetime(year=2000,month=1,day=1)
        end_date=datetime.datetime(year=2000,month=12,day=31)
        assert len(self.d.getQueuedCounts(start_date,end_date)) == 1



