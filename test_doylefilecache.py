import unittest

from app import doylefilecache

class DummyDoyleFile():

    def __init__(self,name):
        self.name=name

class TestDoyleFileCache(unittest.TestCase):

    def setUp(self):
        pass

    def test_init(self):
        c=doylefilecache.DoyleFileCache()
        self.assertEqual(len(c.cache),0)
        self.assertEqual(c.addCount,0)
        self.assertEqual(c.removeCount,0)
        self.assertEqual(c.hitCount,0)

    def test_basic(self):
        c=doylefilecache.DoyleFileCache()
        # should not find a file before it was added
        self.assertEqual(c.getDoyleFile('file1'),None)

        # add a file
        c.addDoyleFile('file1',DummyDoyleFile('file1'))
        self.assertEqual(len(c.cache),1)
        self.assertEqual(c.addCount,1)
        self.assertEqual(c.removeCount,0)
        self.assertEqual(c.hitCount,0)

        x=c.getDoyleFile('file1')
        self.assertNotEqual(x,None)
        self.assertEqual(x.name,'file1')
        self.assertEqual(len(c.cache),1)
        self.assertEqual(c.addCount,1)
        self.assertEqual(c.removeCount,0)
        self.assertEqual(c.hitCount,1)

        c.resetUsedCount()
        u=c.removeUnusedEntries()
        self.assertEqual(len(c.cache),0)
        self.assertEqual(c.addCount,0)
        self.assertEqual(c.removeCount,1)
        self.assertEqual(c.hitCount,0)
        self.assertEqual(len(u),1)
        self.assertEqual(u[0][0],'file1')
        self.assertEqual(u[0][1].name,'file1')


    def test_extended(self):
        c=doylefilecache.DoyleFileCache()

        for i in range(1000):
            c.addDoyleFile('file'+str(i),DummyDoyleFile('file'+str(i)))
        self.assertEqual(len(c.cache),1000)
        self.assertEqual(c.addCount,1000)
        self.assertEqual(c.hitCount,0)
        self.assertEqual(c.removeCount,0)

        c.resetUsedCount()
        for i in range(0,1000,2):
            x=c.getDoyleFile('file'+str(i))
            self.assertNotEqual(x,None)
            self.assertEqual(x.name,'file'+str(i))
        self.assertEqual(c.addCount,0)
        self.assertEqual(c.hitCount,500)
        self.assertEqual(c.removeCount,0)

        u=c.removeUnusedEntries()
        self.assertEqual(len(c.cache),500)
        self.assertEqual(c.addCount,0)
        self.assertEqual(c.hitCount,500)
        self.assertEqual(c.removeCount,500)
        self.assertEqual(len(u),500)

        i=1
        for (file,doyleFile) in u:
            self.assertEqual(file,'file'+str(i))
            self.assertEqual(doyleFile.name,'file'+str(i))
            i=i+2




if __name__ == '__main__':
    unittest.main()