import unittest

from stats import Stats


class TestStats(unittest.TestCase):
    def test_basic(self):
        s = Stats('foo', None, None)
        self.assertEqual(s.format(), 'foo')

    def test_edges(self):
        s = Stats('[%s/%f/%t/%r/%p]', None, None)
        self.assertEqual(s.format(), '[0/0/0/0/ --- ]')
        s.started = 3
        s.total = 5
        s.finished = 1
        self.assertEqual(s.format(), '[3/1/5/2/ 60.0]')

        s.started = 5
        s.finished = 5
        self.assertEqual(s.format(), '[5/5/5/0/100.0]')

    def test_elapsed_time(self):
        s = Stats('[%e]', lambda: 0.4, 0)
        self.assertEqual(s.format(), '[0.400]')

    def test_overall_rate(self):
        times = [0, 5]
        s = Stats('[%o]', lambda: times.pop(0), 0)
        self.assertEqual(s.format(), '[ --- ]')
        s.started = 3
        s.finished = 1
        s.total = 5
        self.assertEqual(s.format(), '[  0.2]')

    def test_escaped_percent(self):
        s = Stats('%%', None, None)
        self.assertEqual(s.format(), '%')

    def test_unrecognized_escape(self):
        s = Stats('%x', None, None)
        self.assertEqual(s.format(), '%x')
