import argparse
import multiprocessing
import sys
import unittest


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.usage = '%(prog)s [options] test_files...'
    ap.add_argument('-j', metavar='N', type=int, dest='jobs',
                    default=multiprocessing.cpu_count(),
                    help=('run N jobs in parallel [default=%(default)s, '
                          'derived from CPUs available]'))
    ap.add_argument('-n', action='store_true', dest='dry_run',
                    help=('dry run (don\'t run commands but act like they '
                          'succeeded)'))
    ap.add_argument('test_files', nargs='*', default=[],
                    help=argparse.SUPPRESS)

    args = ap.parse_args(argv)
    loader = unittest.loader.TestLoader()
    test_names = []
    for fname in args.test_files:
        module_name = fname.replace('/', '').replace('.py', '')
        module_suite = loader.loadTestsFromName(module_name)
        for suite in module_suite:
            test_names.extend(test_case.id() for test_case in suite)

    for name in test_names:
        res, out, err = run_test(name)
        if res:
            print "%s failed:" % name
        else:
            print "%s passed" % name
        for l in out.splitlines():
            print '  %s' % l
        for l in err.splitlines():
            print '  %s' % l


def run_test(name):
    loader = unittest.loader.TestLoader()
    result = TestResult()
    suite = loader.loadTestsFromName(name)
    suite.run(result)
    if result.failures:
        return 1, result.failures[0][1], ''
    if result.errors:
        return 1, result.errors[0][1], ''
    return 0, result.out, result.err


class TestResult(unittest.TestResult):
    def __init__(self, *args, **kwargs):
        super(TestResult, self).__init__(*args, **kwargs)
        self.out = ''
        self.err = ''
        self._mirrorOutput = False
        self.buffer = True

    def stopTest(self, test):
        self.out = sys.stdout.getvalue()
        self.err = sys.stderr.getvalue()
        super(TestResult, self).stopTest(test)

    def addError(self, *args, **kwargs):
        super(TestResult, self).addError(*args, **kwargs)
        self._mirrorOutput = False

    def addFailure(self, *args, **kwargs):
        super(TestResult, self).addError(*args, **kwargs)
        self._mirrorOutput = False


if __name__ == '__main__':
    main()
