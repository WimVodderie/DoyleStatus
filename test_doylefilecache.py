from app import doylefilecache


class DummyDoyleFile:
    def __init__(self, name):
        self.name = name


class TestDoyleFileCache:
    def setUp(self):
        pass

    def test_init(self):
        c = doylefilecache.DoyleFileCache()
        assert len(c.cache) == 0
        assert c.addCount == 0
        assert c.removeCount == 0
        assert c.hitCount == 0

    def test_basic(self):
        c = doylefilecache.DoyleFileCache()
        # should not find a file before it was added
        assert c.getDoyleFile("file1") == None

        # add a file
        c.addDoyleFile("file1", DummyDoyleFile("file1"))
        assert len(c.cache) == 1
        assert c.addCount == 1
        assert c.removeCount == 0
        assert c.hitCount == 0

        x = c.getDoyleFile("file1")
        assert x != None
        assert x.name == "file1"
        assert len(c.cache) == 1
        assert c.addCount == 1
        assert c.removeCount == 0
        assert c.hitCount == 1

        c.resetUsedCount()
        u = c.removeUnusedEntries()
        assert len(c.cache) == 0
        assert c.addCount == 0
        assert c.removeCount == 1
        assert c.hitCount == 0
        assert len(u) == 1
        assert u[0][0] == "file1"
        assert u[0][1].name == "file1"

    def test_extended(self):
        c = doylefilecache.DoyleFileCache()

        for i in range(1000):
            c.addDoyleFile("file" + str(i), DummyDoyleFile("file" + str(i)))
        assert len(c.cache) == 1000
        assert c.addCount == 1000
        assert c.hitCount == 0
        assert c.removeCount == 0

        c.resetUsedCount()
        for i in range(0, 1000, 2):
            x = c.getDoyleFile("file" + str(i))
            assert x != None
            assert x.name == "file" + str(i)
        assert c.addCount == 0
        assert c.hitCount == 500
        assert c.removeCount == 0

        u = c.removeUnusedEntries()
        assert len(c.cache) == 500
        assert c.addCount == 0
        assert c.hitCount == 500
        assert c.removeCount == 500
        assert len(u) == 500

        i = 1
        for (file, doyleFile) in u:
            assert file == "file" + str(i)
            assert doyleFile.name == "file" + str(i)
            i = i + 2


if __name__ == "__main__":
    unittest.main()

