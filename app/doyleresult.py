import threading


class DoyleResult:

    def __init__(self):
        self.lock = threading.Lock()
        self.clear('The information is still being gathered.')

    def clear(self, message):
        self.errorMsg = message
        self.servers = []
        self.serversAlerted = []
        self.executingTests = []
        self.executingTestsAlert = False
        self.queuedTests = []
        self.queuedTestsAlert = False

    def copyFrom(self, newResult):
        with self.lock:
            self.errorMsg = newResult.errorMsg
            self.servers = newResult.servers[:]
            self.serversAlerted = newResult.serversAlerted[:]
            self.executingTests = newResult.executingTests[:]
            self.executingTestsAlert = newResult.executingTestsAlert
            self.queuedTests = newResult.queuedTests[:]
            self.queuedTestsAlert = newResult.queuedTestsAlert


