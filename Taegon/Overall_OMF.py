'''
Created on Jul 27, 2022

Pie/bar chart + break down table of the occurrence of each "observer", "measurer" and "facility"
'''

import sqlite3, plotly.express as px, pandas as pd, textwrap, copy

mpecconn = sqlite3.connect("C:\\Users\\taega\\OneDrive\\Documents\\mpec_files\\mpecwatch_v3.db")
cursor = mpecconn.cursor()

MAX_CHAR_LEN = 30 

def tableNames():
    sql = '''SELECT name FROM sqlite_master WHERE type='table';'''
    cursor = mpecconn.execute(sql)
    results = cursor.fetchall()
    return(results[1::])

def printDict(someDictionary):
    for key,value in someDictionary.items():
        print("{}: {}".format(key,value))

# MPECID : observation count
observers = {}
measurers = {}
stations = {}


for station in tableNames():
    cursor.execute("select * from {}".format(station[0]))
    observations = cursor.fetchall()
    stations.update({station[0]: len(observations)})
    for observation in observations:
        observers[observation[2]] = observers.get(observation[2],0)+1
        measurers[observation[3]] = measurers.get(observation[3],0)+1
        #if observation[2] == '' or observation[3] =='':
            #print(observation[6])

N=10       
def topN(someDictionary, graphTitle, includeNA = False, includeOther = True):
    NA=""
    if includeNA:
        NA = "+NA"
        if '' in someDictionary:     #check observation type
            someDictionary['N/A'] = someDictionary['']
            del someDictionary['']
    else:
        if '' in someDictionary:
            del someDictionary['']
    
    objects11 = dict(sorted(someDictionary.items(), key=lambda x:x[1], reverse = True)[:N])
    for key in copy.copy(list(objects11.keys())):
        if len(key) > MAX_CHAR_LEN:
            new_key = key[:MAX_CHAR_LEN]
            objects11[new_key] = objects11.pop(key)
    objects11 = dict(sorted(objects11.items(), key=lambda x:x[1], reverse = True))
    #printDict(objects11)

    Other=""
    if includeOther:
        Other = "+O"
        objects11.update({"Others":sum(someDictionary.values())-sum(objects11.values())})
        
    #printDict(objects11)
    df = pd.DataFrame(list(objects11.items()), columns=['Objects', 'Count'])
    fig1 = px.pie(df, values='Count', names='Objects', title=graphTitle)
    #fig1.update_layout(legend_itemwidth = 300)
    fig1.write_html("C:\\Users\\taega\\OneDrive\\Documents\\mpec_files\\"+graphTitle+"{}{}.html".format(NA, Other))
    #fig1.show()


''' testing the contents of measurers and observers
res1 = (list(observers.items())[0: 10])
res2 = (list(measurers.items())[0: 10])

print(res1)
print(res2)
'''

topN(observers, "Top {} Observers".format(N))
topN(measurers, "Top {} Measurers".format(N))
topN(stations, "Top {} Facilities".format(N), includeOther = False)

print('finished')
mpecconn.close()