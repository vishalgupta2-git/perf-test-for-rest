"""
perf.py:v0.1
This test suite lays the foundation for a distributed framework
for performance testing of rest APIs
   This version:
   - Accepts API endpoint and the number of requests to be generated
   - Distribute records across multiple worker nodes using redis
   - Collect results from all nodes (using redis)
"""
from logging import exception
import os, sys, time, requests, json    # In-build modules
from pathlib import Path                # In-build modules
utilsPath = str(Path(os.getcwd()).parent.absolute()) + '/utilities'
sys.path.append(utilsPath)              # Edit env info (path for modules)
import redis_utilites as redis_utils    # Import our own modules
import perf_utilities as perf_utils     # Import our own modules
perfUtils = perf_utils.perf_utils()
# redisUtils = redis_utils.redis_utils()

__author__ = "Vishal Gupta"
__copyright__ = "Copyright 2022, Vishal Gupta"
__maintainer__ = "Vishal Gupta"
__email__ = "vishalgupta2@gmail.com"
__status__ = "Early PoC"


def main ():
    assert (perfUtils.setupTestParams(sys.argv)) is True
    perfUtils.createWorkBatches()
    perfUtils.doRequest()
    perfUtils.printSummary()


if __name__ == '__main__':
    main()