import datetime
import operator
import os
from queue import Queue
import statistics
import sqlite3
import threading

# for measuring how long execution takes
from timeit import default_timer as timer

class DoyleQueueDb(threading.Thread):

    TABLE_NAME = "queue_counts"
    DBFILE_NAME = "doyle-q.db"

    def __init__(self, dbFilePath):
        super(DoyleQueueDb, self).__init__()
        self.dbFile = os.path.join(dbFilePath,DoyleQueueDb.DBFILE_NAME)
        self.reqs = Queue()
        self.start()

    def run(self):
        self.db = sqlite3.connect(self.dbFile, detect_types=sqlite3.PARSE_DECLTYPES)

        # check if table exists
        c = self.db.cursor()
        c.execute(f'SELECT name FROM sqlite_master WHERE type="table" AND name="{DoyleQueueDb.TABLE_NAME}"')
        result = c.fetchall()
        c.close()

        # create table if it does not exist yet
        if len(result) == 0 or DoyleQueueDb.TABLE_NAME not in result[0]:
            cmd = f"CREATE TABLE {DoyleQueueDb.TABLE_NAME} (timestamp TIMESTAMP PRIMARY KEY, queuecount INTEGER)"
            print(cmd)
            self.db.execute(cmd)
            self.db.commit()

        while True:
            req, arg, res = self.reqs.get()

            if req == "addCount":
                self._addCount(*arg)
            if req == "getCounts":
                res.put(self._getCounts(*arg))
            if req == "cleanupDatabase":
                res.put(self._cleanupDatabase())
            if req == "--close--":
                break

        self.db.close()

    def quit(self):
        # queue the command to stop the thread
        print("Asking queue db thread to stop")
        self.reqs.put(("--close--", None, None))
        print("Waiting for queue db thread to stop")
        self.join()

    def addCount(self, timestamp, count):
        res = Queue()
        self.reqs.put(("addCount", timestamp, count))

    def _addCount(self, timestamp, count):
        c = self.db.cursor()
        c.execute(f"INSERT INTO {DoyleQueueDb.TABLE_NAME} (timestamp,counts) VALUES (?, ?)" % (timestamp,count) )
        self.db.commit()
        print(f"{count} at {timestamp} : inserted in db")


    def getCounts(self, fromtimestamp, totimestamp):
        res = Queue()
        self.reqs.put(("getCounts", (fromtimestamp, totimestamp), res))
        return res.get()

    def _getCounts(self, fromtimestamp, totimestamp):
        """ Get a list of queue counts between the two timestamps."""
        start = timer()

        c = self.db.cursor()
        c.execute(f'SELECT * FROM {DoyleQueueDb.TABLE_NAME} WHERE timestamp > "%s" AND timestamp < "%s"' % (fromtimestamp, totimestamp))
        entries = c.fetchall()
        c.close()

        end = timer()
        print(f"Got {len(entries)} from db, took {end - start}s")

        return entries

    def cleanupDatabase(self):
        res = Queue()
        self.reqs.put(("cleanupDatabase", None, res))
        return res.get()

    def _cleanupDatabase(self):
        """ Go over the database and remove old entries."""
        start = timer()
        numberOfRowsDeleted = 0
        end = timer()
        print(f"Removed {numberOfRowsDeleted} rows, took {end - start}s")
        return numberOfRowsDeleted
