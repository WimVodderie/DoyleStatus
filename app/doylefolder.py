import os
from enum import Enum


class DoyleFolderType(Enum):
    serverFolder = 1
    queueFolder = 2


class DoyleFolder:
    """ This class collects info for all the tests in its folder."""

    def __init__(self, folderType, folder):
        if not os.path.isdir(folder):
            sys.exit(folder + " is not a valid dir to walk!")
        self.baseFolder = folder
        self.folderType = folderType
        self._clear()

    def _clear(self):
        self.items = []
        self.count = 0

    def update(self, cache):
        self._clear()
        for folder in [f for f in os.listdir(self.baseFolder) if os.path.isdir(os.path.join(self.baseFolder, f))]:
            upgradePending = False
            doyleFileList = []
            for subDir, subDirs, files in os.walk(os.path.join(self.baseFolder, folder)):
                if os.path.split(subDir)[-1].lower() == "upgrade" and len(files) > 0:
                    upgradePending = True
                else:
                    for file in files:
                        if os.path.splitext(file)[1].lower() == ".sh":
                            try:
                                doyleFile = cache.getDoyleFile(subDir, file)
                                if self.folderType == DoyleFolderType.serverFolder:
                                    doyleFile.update(subDir)
                                doyleFileList.append(doyleFile)
                            except (IOError, FileNotFoundError):
                                pass  # something went wrong loading the file, it was probably moved while we were looking

            self.items.append((folder, doyleFileList, upgradePending))
            self.count = self.count + len(doyleFileList)
