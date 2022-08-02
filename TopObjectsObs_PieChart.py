'''
Created on Jul 25, 2022

Pie/bar chart + break down table of how many times each object has been observed (might need to do something like the top 20 most-observed objects, as large survey telescopes observe many thousands of objects)
'''

import sqlite3, matplotlib.pyplot as plt, copy

mpecconn = sqlite3.connect("mpecwatch_v3.db")
cursor = mpecconn.cursor()

#returns a list of all the table names (excluding "MPEC")
def tableNames():
    sql = '''SELECT name FROM sqlite_master WHERE type='table';'''
    cursor = mpecconn.execute(sql)
    results = cursor.fetchall()
    return(results[1::])

objects = {} # Object : observation count

for station in tableNames():
    cursor.execute("select Object from {}".format(station[0]))
    for observation in cursor.fetchall():
        objects[observation[0]] = objects.get(observation[0],0)+1

N = 10 #Top N
objects11 = dict(sorted(objects.items(), key=lambda x:x[1], reverse = True)[:N])
objects10 = copy.copy(objects11)
objects11.update({"Other":sum(objects.values())-sum(objects11.values())})

fig, ax = plt.subplots(1,2)
ax[0].pie(list(objects10.values()), labels = list(objects10.keys()))
ax[0].set_title("Top {}".format(N))
ax[1].pie(list(objects11.values()), labels = list(objects11.keys()))
ax[1].set_title("Top {} + Others".format(N))
#ax[2].table(list(objects11.items()))

#plt.pie(list(objects10.values()), labels = list(objects10.keys()))
for key,value in objects11.items():
    print("{}: {}".format(key,value))
plt.suptitle("Top {} Most Observed Objects".format(N))
plt.show()