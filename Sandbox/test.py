# This creates a file that is exactly 1Kbyte
'''
f=open('PerfData.txt','w')
f.write(1024*'0')
f.close()
'''
'''
import datetime
file_name = 'out_client-{}_'.format(1) + datetime.datetime.now().strftime('%H:%M:%S_%B_%d_%Y')
print file_name
'''
#msg = 'stuff'
#print msg.split(',')

import sqlite3

print sqlite3.sqlite_version
"""
db_connect = sqlite3.connect('PerfData_db.db')
cursor = db_connect.cursor()
# db_close = '''DROP TABLE if exists PerfData'''
# cursor.execute(db_close)
db_init = '''CREATE TABLE if not exists PerfData (
            id INTEGER PRIMARY KEY,
            cpu REAL,
            mem REAL,
            count INTEGER)'''
cursor.execute(db_init)
cursor.execute("INSERT INTO PerfData VALUES(1, 50.2, 75.423, 1)")
cursor.execute("INSERT INTO PerfData VALUES(2, 26.7, 18.123, 5)")
msg = "SELECT cpu FROM PerfData WHERE id=?"
#cursor.execute(msg)
#print cursor.fetchall()
#for records in cursor.fetchall():
#        print records
cursor.execute(msg,(1,))
x = cursor.fetchone()
print x[0]
cursor.execute("UPDATE PerfData SET cpu=? WHERE id=?", (28.3,1))
cursor.execute(msg,(1,))
x = cursor.fetchone()
print x[0], x

cursor.execute("SELECT cpu FROM PerfData WHERE id=?", (1,))
cpu = cursor.fetchone()[0]
print cpu
cursor.execute("SELECT mem FROM PerfData WHERE id=?", (1,))
mem = cursor.fetchone()[0]
print mem
"""
db_connect2 = sqlite3.connect('client_performance.db')
cursor2 = db_connect2.cursor()
cursor2.execute("INSERT INTO PerfData VALUES(?, 0, 0)", (1,))
cursor2.execute("SELECT cpu FROM PerfData WHERE client_id=?", (1,))
print cursor2.fetchone()



