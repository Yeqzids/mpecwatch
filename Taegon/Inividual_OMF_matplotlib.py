'''
Created on Aug 17, 2022

@author: TRule
'''

import sqlite3, matplotlib.pyplot as plt, plotly.express as px, pandas as pd

mpecconn = sqlite3.connect("mpecwatch_v3.db")
cursor = mpecconn.cursor()

def printDict(someDictionary):
    for key,value in someDictionary.items():
        print("{}: {}".format(key,value))

def tableNames():
    sql = '''SELECT name FROM sqlite_master WHERE type='table';'''
    cursor = mpecconn.execute(sql)
    results = cursor.fetchall()
    return(results[1:2])

#creating and writing Pie chart to html
def topN(someDictionary, graphTitle, station):
    if len(someDictionary) > 10: #if more than 10 data points DO top 10 + other
        topObjects = dict(sorted(someDictionary.items(), key=lambda x:x[1], reverse = True)[:N])
        topObjects.update({"Other":sum(someDictionary.values())-sum(topObjects.values())})
    else: #otherwise show all data points
        topObjects = dict(sorted(someDictionary.items(), key=lambda x:x[1], reverse = True))
    
    if '' in topObjects:     #check observation type
        topObjects['N/A'] = topObjects['']
        del topObjects['']
    
    data = pd.DataFrame(topObjects, index=[0])
    fig = px.pie(data, title=graphTitle)
    plt.figure(graphTitle)
    plt.pie(list(topObjects.values()), labels = list(topObjects.keys()))
    plt.title(graphTitle)
    #fig.savefig(graphTitle[7::] + station[0] +".html")
    fig.show()
    
N = 10
tables = tableNames()
for station in tables:
    observers = {}
    measurers = {}
    facilities = {}
    cursor.execute("select * from {}".format(station[0]))
    observations = cursor.fetchall()
    for observation in observations:
        observers[observation[2]] = observers.get(observation[2],0)+1
        measurers[observation[3]] = measurers.get(observation[3],0)+1
        facilities[observation[4]] = facilities.get(observation[4],0)+1
    topN(observers, "Top {} Observers".format(N), station)
    topN(measurers, "Top {} Measurers".format(N), station)
    topN(facilities, "Top {} Facilities".format(N), station)
    
#plt.show()
    