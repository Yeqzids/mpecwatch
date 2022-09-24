'''
Created on Jul 25, 2022

Pie/bar chart + break down table of how many times each object has been observed (might need to do something like the top 20 most-observed objects, as large survey telescopes observe many thousands of objects)
'''

import sqlite3, pandas as pd, plotly.express as px

mpecconn = sqlite3.connect("../mpecwatch_v3.db")
cursor = mpecconn.cursor()

#prints the content of a dictionary
def printDict(someDictionary):
    for key,value in someDictionary.items():
        print("{}: {}".format(key,value))
        
#returns a list of all the table names (excluding "MPEC")
def tableNames():
    sql = '''SELECT name FROM sqlite_master WHERE type='table';'''
    cursor = mpecconn.execute(sql)
    results = cursor.fetchall()
    return(results[1::])

def topN(objects_dict, includeOther = False):
    if includeOther:
        other = "+Other"
        topObjects = dict(sorted(objects_dict.items(), key=lambda x:x[1], reverse = True)[:N])
        topObjects.update({"Others":sum(objects_dict.values())-sum(topObjects.values())})
    else:
        other = ""
        topObjects = dict(sorted(objects_dict.items(), key=lambda x:x[1], reverse = True)[:N])
    
    df = pd.DataFrame(list(topObjects.items()), columns=['Objects', 'Count'])
    fig1 = px.pie(df, values='Count', names='Objects', title="Top {} Most Observed Objects {}".format(N, other))
    fig1.write_html("../www/stats/T10Objects{}.html".format(other))
    
objects = {} # Object : observation count

for station in tableNames():
    cursor.execute("select Object from {}".format(station[0]))
    for observation in cursor.fetchall():
        objects[observation[0]] = objects.get(observation[0],0)+1

N = 10 #Top N
topN(objects, False)
topN(objects, True)

print('finished')
mpecconn.close()
