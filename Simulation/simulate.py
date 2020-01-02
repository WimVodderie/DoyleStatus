import sys
import os
import shutil
import random

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
shutil.rmtree(rootFolder)
# create root folder
os.mkdir(rootFolder)
# create queues folders
os.mkdir(queueFolder)
queueFolders = []
for q in range(numberOfQueues):
    qf = f"Queue-{q+1}"
    queueFolders.append(qf)
    os.mkdir(os.path.join(queueFolder,qf))
# create server folders
os.mkdir(serverFolder)
serverFolders = []
for s in range(numberOfServers):
    sf = f"Server-{s+1}"
    serverFolders.append(sf)
    os.mkdir(os.path.join(serverFolder,sf))

# keep track of queued and running tests

queuedTests = {}
runningTests = {}

testNumber = 1

while True:
    # should we add a new test ?
    if len(queuedTests) < maximumNumberOfQueuedTests:
        #
        # queue a new test
        #
        # determine execution time and queue folder
        executionTime = random.choice(testDurations)
        qf = random.choice(queueFolders)

        testName = f"Test-{testNumber:05}-{executionTime}"

        # contents of the test file

        #!/bin/ksh
#
# QueueName: DOYLE-ARIANE-2
# TargetName: TestCaseSimulation.install
# ProjectRef: xse060x/InstallersDoyle/Kourou/10878
# ReleaseLogs: u:\pgxbe\logs\20180621-134301-9812-xse060x-InstallersDoyle-Kourou
# ScriptFile: u:\pgxbe\releases\xse060x\InstallersDoyle\Kourou\10878\Doyle;Q=DOYLE-ARIANE-2;T=TestCaseSimulation.install;A.sh

function ReportSkipped
{
    echo "The test is skipped. $1"
    echo "'Mail successfully sent' is echoed to block mail."
}

export XBERELEASELOGPATH="u:\\pgxbe\\logs\\20180621-134301-9812-xse060x-InstallersDoyle-Kourou"
export XBEHOME="u:\\pgxbe\\releases\\xse060x\\InstallersDoyle\\Kourou\\10878"
export XBEDOYLESCRIPT="Doyle;Q=DOYLE-ARIANE-2;T=TestCaseSimulation.install;A.sh"
export tfsbuildflavor="Release"
export tfsbuildid="33451"
export tfsbuildname="xse060x_InstallersDoyle_Kourou"
export tfsbuildplatform="Any CPU"
export tfsbuildproject="http://tfs:8080/tfs/defaultcollection"
export tfsbuildprojectname="PGX"

if [ "$(xbe_getlr -t xse060x InstallersDoyle Kourou)" != "10878" ]
then
    ReportSkipped "There is a later release."; exit 0
fi

if [ "$(/usr/bin/find "${XBEHOME//\\//}" -maxdepth 1 -name "${XBEDOYLESCRIPT}.lock" -mmin -720 -printf 1)" == "1" ]
then
    ReportSkipped "It was already executed recently."; exit 0
fi

. "${XBEHOME//\\//}/${XBEDOYLESCRIPT}" $1





        pass

    # any server idle ?


# task that randomly adds tests to a queue, name of the test determines average execution time


# task that pulls tests from a queue and executes it on a server, randomize execution time
