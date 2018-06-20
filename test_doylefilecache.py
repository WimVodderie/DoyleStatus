import unittest

from app import doylefilecache

#class DummyDoyleFile():


class TestDoyleFileCache(unittest.TestCase):

    def setUp(self):
        pass

    def test_init(self):
        c=doylefilecache.DoyleFileCache()
        self.assertEqual(len(c.cache),0)
        self.assertEqual(c.addCount,0)
        self.assertEqual(c.removeCount,0)
        self.assertEqual(c.hitCount,0)


if __name__ == '__main__':
    unittest.main()