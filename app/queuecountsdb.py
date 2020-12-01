import datetime
import statistics
import sqlite3
import traceback

# for measuring how long execution takes
from timeit import default_timer as timer


class QueueCountsDb:
    """Helper class to buffer queue counts. This class also has the database so
    make sure it's methods are ran in the same thread as other db actions."""

    # old table, does not need to be present
    TABLE_NAME_QUEUECOUNTS = "queue_counts"

    # new table
    TABLE_NAME_QUEUECOUNTS2 = "queue_counts2"

    def __init__(self, db):
        self.db = db

        # check if the table we need exists
        c = self.db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [x[0] for x in c.fetchall()]
        c.close()

        # when the old table is present some more conversion is needed
        self.conversionNeeded = QueueCountsDb.TABLE_NAME_QUEUECOUNTS in table_names

        # new table that stores min/max/sum per date / hour
        if QueueCountsDb.TABLE_NAME_QUEUECOUNTS2 not in table_names:
            self.db.execute(f"CREATE TABLE {QueueCountsDb.TABLE_NAME_QUEUECOUNTS2} (date DATE, hour INTEGER, min INTEGER, max INTEGER, count INTEGER, sum INTEGER)")
            self.db.commit()

    def add(self, timestamp, count , commit=True):
        """ Add a timestamp / count entry to the row for that date / hour."""
        try:
            c = self.db.cursor()
            c.execute(f"SELECT min,max,count,sum FROM {QueueCountsDb.TABLE_NAME_QUEUECOUNTS2} WHERE date = {timestamp.date()} AND hour = {timestamp.hour}")
            result = c.fetchall()
            if len(result) == 0:
                c.execute(f"INSERT INTO {QueueCountsDb.TABLE_NAME_QUEUECOUNTS2} (date,hour,min,max,count,sum) VALUES ({timestamp.date()},{timestamp.hour},{count},{count},1,{count})")
            else:
                new_min = result[0][0] if result[0][0] <= count else count
                new_max = result[0][1] if result[0][1] >= count else count
                new_count = result[0][2] + 1
                new_sum = result[0][3] + count
                c.execute(f"UPDATE {QueueCountsDb.TABLE_NAME_QUEUECOUNTS2} SET min=?,max=?,count=?,sum=? WHERE date = {timestamp.date()} AND hour = {timestamp.hour}", (new_min, new_max, new_count, new_sum))
            c.close()

            if commit:
                self.db.commit()
        except:
            print(f"Updating queuecountsdb failed with exception: {traceback.format_exc()}")

    def getChartData(self, date):
        """ Get chart data (min/avg/max) for the number of tests queued on the requested day."""
        start = timer()

        c = self.db.cursor()
        c.execute(f"SELECT hour,min,max,count,sum FROM {QueueCountsDb.TABLE_NAME_QUEUECOUNTS2} WHERE date = {date}")
        result = c.fetchall()
        c.close()

        result.sort()
        chartData = []
        for r in result:
            chartData.append((datetime.datetime.combine(date, datetime.time(r[0])), r[1], int(r[4] / r[3]), r[2]))

        end = timer()
        print(f"Got {len(chartData)} from db, took {end - start}s")
        return chartData


    def convertOldData(self):
        """ Read some records from the old table and convert to the new table."""

        if self.conversionNeeded:
            # read oldest record
            c = self.db.cursor()
            c.execute(f"SELECT * FROM {QueueCountsDb.TABLE_NAME_QUEUECOUNTS}")
            result = c.fetchmany(1)
            c.close()

            if len(result)==0:
                # table is empty, delete it
                c = self.db.cursor()
                c.execute(f"DROP TABLE {QueueCountsDb.TABLE_NAME_QUEUECOUNTS}")
                c.close
                self.conversionNeeded = False

                print(f"Conversion ended, table deleted")

            else:
                start = timer()

                # get all records for that hour
                date = result[0][0].date()
                hour = result[0][0].hour

                fromTimeStamp = datetime.datetime.combine(date,datetime.time(hour,minute=0,second=0))
                toTimeStamp = datetime.datetime.combine(date,datetime.time(hour,minute=59,second=59,microsecond=999999))

                c = self.db.cursor()
                c.execute(f"SELECT * FROM {QueueCountsDb.TABLE_NAME_QUEUECOUNTS} WHERE timestamp BETWEEN ? AND ?", (fromTimeStamp, toTimeStamp))
                result = c.fetchall()
                c.close()

                # push them to the new table (we will commit at the end)
                for r in result:
                    self.add(r[0],r[1], commit=False)

                # remove records from old table
                c = self.db.cursor()
                c.execute(f"DELETE FROM {QueueCountsDb.TABLE_NAME_QUEUECOUNTS} WHERE timestamp BETWEEN ? AND ?", (fromTimeStamp, toTimeStamp))
                c.close

                self.db.commit()

                end = timer()
                print(f"Migrated {len(result)} entries between {fromTimeStamp} and {toTimeStamp}, took {end - start}s")


if __name__ == "__main__":
    db = sqlite3.connect("/media/wim/DATA/Xeikon/doyledb-20201023-2111.db", detect_types=sqlite3.PARSE_DECLTYPES)

    qc = QueueCountsDb(db)

    while qc.conversionNeeded:
        qc.convertOldData()

    db.close()
