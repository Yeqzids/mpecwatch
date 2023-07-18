import sqlite3, plotly.express as px, pandas as pd, json

mpecconn = sqlite3.connect("../mpecwatch_v3.db")
cursor = mpecconn.cursor()

mpccode = '../mpccode.json'
with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)
    
def printDict(someDictionary):
    for key,value in someDictionary.items():
        print("{}: {}".format(key,value))

def tableNames():
    sql = '''SELECT name FROM sqlite_master WHERE type='table';'''
    cursor = mpecconn.execute(sql)
    results = cursor.fetchall()
    return(results[1::])

#creating and writing Pie chart to html
def topN(someDictionary, graphTitle, station, includeNA = False):    
    if includeNA:
        titleNA = "+NA"
        if '' in someDictionary:     #check observation type
            someDictionary['N/A'] = someDictionary['']
            del someDictionary['']
    else:
        titleNA=""
        if '' in someDictionary:
            del someDictionary['']

    if 0 in someDictionary:
        del someDictionary[0]
    
    if len(someDictionary) > N: #if more than N data points DO top 10 + other
        topObjects = dict(sorted(someDictionary.items(), key=lambda x:x[1], reverse = True)[:N])
        topObjects.update({"Others":sum(someDictionary.values())-sum(topObjects.values())})
    else: #otherwise show all data points
        topObjects = dict(sorted(someDictionary.items(), key=lambda x:x[1], reverse = True))
    
    #printDict(topObjects)
    df = pd.DataFrame(list(topObjects.items()), columns=['Objects', 'Count'])
    fig1 = px.pie(df, values='Count', names='Objects', title=station[-3:] + " " + mpccode[station[-3:]]['name'] + " | " + graphTitle)
    if len(topObjects) == 0:
       fig1.add_annotation(text="No Data Available",
                  xref="paper", yref="paper",
                  x=0.3, y=0.3, showarrow=False)
    else:
        fig1.update_traces(textposition='inside', textinfo='percent')
        fig1.update_layout(hoverlabel=dict(
            font=dict(size=10),
            max_length=10,
        )
    )

    fig1.write_html("../www/byStation/OMF/"+station+"_"+graphTitle.replace(' ', '_')+"{}.html".format(titleNA))

N = 10 #Top limit of objects to show individually
#for station in tableNames():
for i in range(1):
    #station = station[0]
    station = "station_010"
    observers = {}
    measurers = {}
    facilities = {}
    cursor.execute("select * from {}".format(station))
    observations = cursor.fetchall()
    for observation in observations:
        observers[observation[2]] = observers.get(observation[2],0)+1
        measurers[observation[3]] = measurers.get(observation[3],0)+1
        facilities[observation[4]] = facilities.get(observation[4],0)+1
    
    #doesnt include NA:
    try:
        topN(observers, "Top {} Observers".format(N), station)
        topN(measurers, "Top {} Measurers".format(N), station)
        topN(facilities, "Top {} Facilities".format(N), station)
    except Exception as e:
        print(e)
    
    #includes NA:
    #topN(observers, "Top {} Observers".format(N), station[0], True)
    
    print(station + " done")
    
mpecconn.close()
print('finished')
    
