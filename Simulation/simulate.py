import sys
import os
import shutil
import random
from dataclasses import dataclass
import datetime
import time

# for now fixed number of queues and servers
numberOfQueues = 10
numberOfServers = 5

testDurations = [30, 60, 120, 300, 600 ]

# assume all servers can process all queues

#
maximumNumberOfQueuedTests = 100

rootFolder = os.path.abspath(os.path.join(os.path.dirname(__file__),"../TestData"))
queueFolder = os.path.join(rootFolder,"TestQueues")
serverFolder = os.path.join(rootFolder,"TestServers")


#
# prepare the folder structure for these tests
#
# cleanup
shutil.rmtree(rootFolder,ignore_errors=True)
# create root folder
os.mkdir(rootFolder)
# create queues folders
os.mkdir(queueFolder)
queues = []
for q in range(numberOfQueues):
    qf = f"Queue-{q+1}"
    queues.append(qf)
    os.mkdir(os.path.join(queueFolder,qf))

# create server folders
os.mkdir(serverFolder)
servers = {}
for s in range(numberOfServers):
    sf = f"Server-{s+1}"
    servers[sf]=None
    os.mkdir(os.path.join(serverFolder,sf))

@dataclass
class QueuedInfo:
    testFile:str
    executionTime:int

@dataclass
class RunningInfo:
    testFile:str
    doneAt:datetime.datetime

# keep track of queued tests
testNumber = 1
queuedTests = []

while True:
    # should we add a new test ?
    if len(queuedTests) < maximumNumberOfQueuedTests:
        #
        # queue a new test
        #
        # determine execution time and queue folder
        executionTime = random.choice(testDurations)
        qf = random.choice(queues)

        newFileName = os.path.join(queueFolder,qf,f"Test-{testNumber:05}-{executionTime}.sh")

        # contents of the test file
        with open(newFileName,"wt") as f:
            f.write('export XBEHOME="u:/pgxbe/releases/B999/InstallersDoyle/Kourou/42"\n')
            f.write(f'# TargetName: TestCase{executionTime}\n')
            f.write('export tfsbuildid="33451"\n')
            f.write('# ScriptFile: testfile;A.sh\n')

        queuedTests.append(QueuedInfo(newFileName,executionTime))
        print(f"Added test {newFileName}")

        testNumber+=1

    # any busy server done ?
    now = datetime.datetime.now()
    for s,r in servers.items():
        if r is not None:
            if r.doneAt < now:
                # this test has finished
                print(f"Deleted test {r.testFile}")
                os.remove(r.testFile)
                servers[s]=None

    # any server idle ? -> start executing the oldest queued test
    idleServers=[s for s,r in servers.items() if r is None]
    if len(idleServers)>0 and len(queuedTests)>0:
        s = random.choice(idleServers)
        test = queuedTests.pop(0)
        newTestFile=os.path.join(serverFolder,s,os.path.basename(test.testFile))
        os.rename(test.testFile,newTestFile)
        servers[s]=RunningInfo(newTestFile,now+datetime.timedelta(seconds=test.executionTime))
        print(f"Started executing {test.testFile} on {s}")

    # sleep for a while
    time.sleep(1)

