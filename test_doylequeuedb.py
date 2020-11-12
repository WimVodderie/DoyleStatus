import os
import datetime

from app import doylefiledb

#testDbPath="./TestData/TestDb"
testDbPath="/tmp"
testDbBackupPath="/tmp"

class TestDoyleQueueDb:
    def setup(self):
        dbFile = f"{testDbPath}/{doylefiledb.DoyleFileDb.DBFILE_NAME}"
        if os.path.exists(dbFile):
            os.remove(dbFile)
        self.d = doylefiledb.DoyleFileDb(testDbPath,testDbBackupPath)

    def teardown(self):
        self.d.quit()

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



