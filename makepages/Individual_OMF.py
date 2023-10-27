import sqlite3, plotly.express as px, pandas as pd, json
from datetime import date

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
    
    #if there are no data points, add annotation
    if len(topObjects) == 0:
       fig1.add_annotation(text="No Data Available",
                  xref="paper", yref="paper",
                  x=0.3, y=0.3, showarrow=False)
    

    fig1.write_html("../www/byStation/OMF/"+station+"_"+graphTitle.replace(' ', '_')+"{}.html".format(titleNA))

def time_frequency_figure(station):
    yearly = {'summer':0, 'autumn':0, 'winter':0, 'spring':0}
    weekly = {'Monday':0, 'Tuesday':0, 'Wednesday':0, 'Thursday':0, 'Friday':0, 'Saturday':0, 'Sunday':0}
    #daily = {} unable to use daily since data only includes the day of oberservation, no the time

    cursor.execute("select Time from {}".format(station))
    for time in cursor.fetchall():
        time = int(time[0])
        year = date.fromtimestamp(time).year
        month = date.fromtimestamp(time).month
        day = date.fromtimestamp(time).day
        if month in [6,7,8]:
            yearly['summer'] += 1
        elif month in [9,10,11]:
            yearly['autumn'] += 1
        elif month in [12,1,2]:
            yearly['winter'] += 1
        elif month in [3,4,5]:
            yearly['spring'] += 1
        
    df = pd.DataFrame(list(yearly.items()), columns=['Season', 'Count'])
    print(df)
    graph_title = station[-3:] + " " + mpccode[station[-3:]]['name']
    fig1 = px.pie(df, values='Count', names='Season', title = graph_title + " | Seasonal Frequency")
    fig1.write_html("../www/byStation/OMF/"+station+"_seasonal.html".replace(' ', '_'))



N = 10 #Top limit of objects to show individually
for station in mpccode.keys():
#for i in range(1):
    #station = "station_J95"
    station = "station_" + station
    observers = {}
    measurers = {}
    facilities = {}
    try:
        cursor.execute("select Observer, Measurer, Facility, Time from {}".format(station))
        message = "{} done".format(station)
    except:
        message = "Table {} does not exist".format(station)
        
        
    for mpec in cursor.fetchall():
        if (len(mpec[0]) > 30):
            observer = mpec[0][:30] + "..."
            observers[observer] = observers.get(observer,0)+1
        else:
            observers[mpec[0]] = observers.get(mpec[0],0)+1
        measurers[mpec[1]] = measurers.get(mpec[1],0)+1
        facilities[mpec[2]] = facilities.get(mpec[2],0)+1
    
    #doesnt include NA:
    try:
        topN(observers, "Top {} Observers".format(N), station)
        topN(measurers, "Top {} Measurers".format(N), station)
        topN(facilities, "Top {} Facilities".format(N), station)
        time_frequency_figure(station)
        #day week frequency

    except Exception as e:
        message = e
    
    #includes NA:
    #topN(observers, "Top {} Observers".format(N), station[0], True)
    
    print(message)
    
mpecconn.close()
print('finished')
    
