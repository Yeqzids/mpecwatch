'''
Created on Jul 27, 2022

Pie/bar chart + break down table of the occurrence of each "observer", "measurer" and "facility"
'''

import sqlite3, matplotlib.pyplot as plt

mpecconn = sqlite3.connect("mpecwatch_v3.db")
cursor = mpecconn.cursor()

def tableNames():
    sql = '''SELECT name FROM sqlite_master WHERE type='table';'''
    cursor = mpecconn.execute(sql)
    results = cursor.fetchall()
    return(results[1::])

# MPECID : observation count
observers = {}
measurers = {}
facilities = {}


for station in tableNames():
    cursor.execute("select * from {}".format(station[0]))
    for observation in cursor.fetchall():
        observers[observation[2]] = observers.get(observation[2],0)+1
        measurers[observation[3]] = measurers.get(observation[3],0)+1
        facilities[observation[4]] = facilities.get(observation[4],0)+1

N=10
#sum of table values = 4396944. total entries
       
def topN(someDictionary, graphTitle):
    objects11 = dict(sorted(someDictionary.items(), key=lambda x:x[1], reverse = True)[:N])
    objects11.update({"Other":sum(someDictionary.values())-sum(objects11.values())})
    objects11['N/A'] = objects11['']
    del objects11['']
    printDict(objects11)
    plt.pie(list(objects11.values()), labels = list(objects11.keys()))
    plt.title(graphTitle)
    plt.figure()
    
def printDict(someDictionary):
    for key,value in someDictionary.items():
        print("{}: {}".format(key,value))

topN(observers, "Top {} Observers".format(N))
topN(measurers, "Top {} Measurers".format(N))
topN(facilities, "Top {} Facilities".format(N))

plt.show()
