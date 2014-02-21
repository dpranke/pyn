#!/usr/bin/python

import cProfile
import pstats

from main import _real_main

def profile():
    return _real_main()

if __name__ == '__main__':
    cProfile.run('profile()', '.profiler_data')
    p = pstats.Stats('.profiler_data')
    p.strip_dirs()
    p.sort_stats('time')
    p.print_stats(50)

