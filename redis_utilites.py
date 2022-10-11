"""
redis_utilites.py:v0.1
This module provides all the utilities needed for co-ordinating perf testing using redis
   This version supports:
   - Get tasks from redis by node ID
   - Update results
   - Get results

There is currently no handling for redis errors
"""
from curses.ascii import isdigit
import redis

__author__ = "Vishal Gupta"
__copyright__ = "Copyright 2022, Vishal Gupta"
__maintainer__ = "Vishal Gupta"
__email__ = "vishalgupta2@gmail.com"
__status__ = "Early PoC"

class redis_utils():
    redisHost = 'localhost'
    redisPort = 6379
    # We should make client global instead of connecting in each def
    def setKey(self, key, val):
        client = redis.Redis(host=self.redisHost, port=self.redisPort, charset="utf-8", decode_responses=True)
        client.set(key, val)
    
    def getKey(self, key):
        client = redis.Redis(host=self.redisHost, port=self.redisPort, charset="utf-8", decode_responses=True)
        return client.get(key)
        
