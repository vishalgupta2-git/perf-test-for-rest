"""
perf_utilities.py:v0.1
This module provides all the utilities needed for perf testing of Rest APIs
   This version supports:
   - Argument count validation
   - Link reachablility (doesn't do a pattern check on link)
   - Create requests
   - Aggregates requests
"""
from argparse import ArgumentError
from ast import Return
from logging import exception
import os, sys, time, requests, statistics    # In-build modules
import redis_utilites as redis_utils    # Import our own modules
redisUtils = redis_utils.redis_utils()

__author__ = "Vishal Gupta"
__copyright__ = "Copyright 2022, Vishal Gupta"
__maintainer__ = "Vishal Gupta"
__email__ = "vishalgupta2@gmail.com"
__status__ = "Early PoC"

class perf_utils():
    executionMode = 'master'
    slaveID = 1
    restEndpoint = ''
    requestType = 'get'     # For future extension to support more request types
    totalCalls = 0
    expectedReturn = 200    # To be implemented later to make sure calls are actually working properly
    batchSize = 100         # Batches in which the rest calls will be made (TBD fix hardcoding)
    numNodes = 1            # Number of nodes running tests, including master
    numBatches = 0          # Batches to be executed
    lastBatch = 0


    def scriptHelp(self):
        # This function prints script help
        ## TBD More detailed & unambiguous info to be added to usage ##
        print("\n############ Script Help ############")
        print("This script can run in master of slave mode")
        print("----- Master Mode -----")
        print("Usage: python3 perf.py master <count of test nodes including master> <Link under test> <total get calls to make> <redis host> <redis port>")
        print("Example: python3 perf.py master 4 http://google.com 5000 localhost 6379")
        print("\n----- Slave Mode -----")
        print("Usage: python3 perf.py slave <slave ID> <redis host> <redis port>")
        print("Example: python3 perf.py slave 2 localhost 6379")
        print("Slave node ID range is 2-99, as ID 1 is reserver for master")
        print("#####################################\n")

    def isLinkReachable(self, restEndpoint):
        '''
        This function will validate link passed for testing is valid
        TBD: Implement link validation. For now we are only checking for status 200
        '''
        res = requests.get(restEndpoint, verify=False)
        if res.status_code != 200:
            return False
        return True

    def setSlaveArgs(self, args):
        '''
        This function validates and sets slave arguments.
        We have no checks for duplicate slave IDs
        '''
        if not args[2].isdigit():
            self.scriptHelp()
            raise ValueError("Invalid Slave ID passed, see usage above")
        
        if (int(args[2]) < 2) or (int(args[2]) > 99):
            self.scriptHelp()
            raise ValueError("Slave ID must be between 2 & 99, see usage above")

        # TBD check arg[3] redis host validity

        if not args[4].isdigit():
            self.scriptHelp()
            raise ValueError("Invalid Redis port passed, see usage above")
        
        # Validations passed, set slave arguments
        self.executionMode = 'slave'
        self.slaveID = args[2]
        redisUtils.redisHost = args[3]
        redisUtils.redisPort = int(args[4])

        # Make sure slave Id is 2 digits
        if len(self.slaveID) == 1:
            self.slaveID = f'0{self.slaveID}'
        return True

    def setMasterArgs(self, args):
        '''
        This function validates and sets master arguments.
        We have no checks for duplicate slave IDs
        '''
        # Node count
        if not args[2].isdigit():
            self.scriptHelp()
            raise ValueError("Invalid node count, see usage above")

        if (int(args[2]) < 2) or (int(args[2]) > 99):
            self.scriptHelp()
            raise ValueError("Slave ID must be between 2 & 99, see usage above")

        # Rest url
        if self.isLinkReachable(args[3]) is False:
            self.scriptHelp()
            raise ValueError("Invalid or unreachable link passed, see usage above")

        # Total Calls
        if not args[4].isdigit():
            self.scriptHelp()
            raise ValueError("Invalid call count, see usage above")
        
        # Redis port
        if not args[6].isdigit():
            self.scriptHelp()
            raise ValueError("Invalid Redis port passed, see usage above")
        
        # Set variables
        self.numNodes = int(args[2])
        self.restEndpoint = args[3]
        self.totalCalls = args[4]
        redisUtils.redisHost = args[5]
        redisUtils.redisPort = int(args[6])
        self.slaveID = '01'
        return True
        
    def setupTestParams(self, args):
        '''
        This function verifies the arguments passed to the test script &
        setups the execution mode
        '''
        if (len(args) == 2) and (args[1].lower() == '--help'):
            self.scriptHelp()   # Print usage and exit
            return False

        if (len(args) == 5) and (args[1].lower() == 'slave'):
            if self.setSlaveArgs(args) is True:
                return True

        if len(args) != 7:
            self.scriptHelp()
            raise ValueError("Invalid number of Arguments passed, see usage above")

        if (len(args) == 7) and (args[1].lower() == 'master'):
            if self.setMasterArgs(args) is True:
                return True

        if (len(args) == 7) and (args[1].lower() != 'master'):
            self.scriptHelp()
            raise ValueError("Invalid execution mode passed, see usage above")

    def setRedisTaskCount(self, slaveID, tasks, lastBatchOnNode=False):
        if slaveID < 10:
            slaveID = f'0{slaveID}'
        key = f'slave_{slaveID}_tasks'
        val = tasks
        redisUtils.setKey(key, val)
        # Insert batches for each slave node
        for i in range (tasks):
            key = f'slave_{slaveID}_task_{i+1}'
            val = self.batchSize
            if (i == tasks - 1) and (self.lastBatch > 0) and (lastBatchOnNode is True):
                val = self.lastBatch
            redisUtils.setKey(key, val)   

    def insertBatches(self, batchesPerNode, unEqualBatches):
        '''
        This function will insert batches into redis for slave nodes to execute
        '''
        # Insert task counts for each slave node
        for i in range(self.numNodes):
            tasks = batchesPerNode
            if i < unEqualBatches:
                tasks += 1
            if i == unEqualBatches - 1:
                self.setRedisTaskCount(i + 1, tasks, True)
            else:
                self.setRedisTaskCount(i + 1, tasks)

    def createWorkBatches(self):
        if self.executionMode == 'slave':
            print("This is a slave node, skipping batching")
            return
        redisUtils.setKey('restEndpoint', self.restEndpoint)
        redisUtils.setKey('requestType', self.requestType)
        self.numBatches = int(int(self.totalCalls) / int(self.batchSize))
        self.lastBatch = int(self.totalCalls) % int(self.batchSize)
        if self.lastBatch > 0:
            self.numBatches += 1 # Add a batch for left over calls
        
        print(self.totalCalls, self.numBatches, self.lastBatch)
        batchesPerNode = int(self.numBatches / self.numNodes)    
        unEqualBatches = self.numBatches % self.numNodes  
        print (batchesPerNode, unEqualBatches)  
        self.insertBatches(batchesPerNode, unEqualBatches)    # Send batches to redis
    
    def getBatchCountFromRedis(self):
        key = f'slave_{self.slaveID}_tasks'
        print(key)
        return int(redisUtils.getKey(key))

    def getBatchFromRedis(self, taskID):
        key = f'slave_{self.slaveID}_task_{taskID}'
        restEndpoint = redisUtils.getKey('restEndpoint')
        numRequests = int(redisUtils.getKey(key))
        requestType = redisUtils.getKey('requestType') 
        return(restEndpoint, numRequests, requestType)

    def updateResultInRedis(self, taskID, result, response):
        key = f'slave_{self.slaveID}_task_{taskID}_result'
        val = f'{result}::{response}'
        print(key, val)
        redisUtils.setKey(key, val)
        print(redisUtils.getKey(key))

    def getResultsFromReddis(self, taskID):
        key = f'slave_{self.slaveID}_task_{taskID}_result'
        return (redisUtils.getKey(key).split('::'))


    def doRequest(self):
        '''
        This function will take the request types and execute them n number of times
        It will also return average response time for the batch
        TBD: Need to return more percentiles, min, max etc
        '''
        totalTasks = self.getBatchCountFromRedis()
        for i in range(totalTasks):
            restEndpoint, numRequests, requestType = self.getBatchFromRedis(i + 1)
            if requestType != 'get':
                self.updateResultInRedis(i + 1, 'Failed', "Invalid Request Type")
                raise ValueError (f'Request type {requestType} is not supported, only get is supported in current version')
            responseTimes = []
            print(f'task count: {i + 1}, requests in task: {numRequests}')
            for j in range (numRequests):
                res = requests.get(restEndpoint, verify=False)
                responseTimes.append(res.elapsed.microseconds)
            print(responseTimes)
            meanResponseTime = int(statistics.mean(responseTimes))
            print(meanResponseTime)
            self.updateResultInRedis(i + 1, 'Passed', meanResponseTime)

    def printSummary(self):
        '''
        This function currently checks only for master results, need to extend
        Looping over all the nodes will do the trick
        '''
        if self.executionMode == 'slave':
            print("This is a slave node, skipping result collection & aggregation")
            return
        errorCount = 0
        averages = []   # TBD, if we need to scale, we will need to fix this line
        totalTasks = self.getBatchCountFromRedis()
        for i in range(totalTasks):
            result, value = self.getResultsFromReddis(i + 1)
            if result == 'Failed':
                errorCount = errorCount + 1
            else:
                averages.append(int(value))
        print(averages)
        print(f'Overall average = {statistics.mean(averages)}')