# This creates a file that is exactly 1Kbyte
'''
f=open('test.txt','w')
f.write(1024*'0')
f.close()
'''
'''
import datetime
file_name = 'out_client-{}_'.format(1) + datetime.datetime.now().strftime('%H:%M:%S_%B_%d_%Y')
print file_name
'''
msg = 'stuff'
print msg.split(',')
