#!/usr/bin/env

import asynchat
import asyncore
import socket
import errno
import threading
import logging, logging.handlers
import tempfile
import time
import random


LOG_FILENAME = 'client_log.log'

class BenchmarkClient(asynchat.async_chat):

    def __init__(self, addr, id, chunksize, runtime, filesize):
        asynchat.async_chat.__init__(self)
        self.addr = addr
        self.id = id
        self.chunksize = chunksize
        self.runtime = runtime
        self.filesize = filesize
        self.incoming = [] # Buffer for incoming messages from server
        self.set_terminator('\n')

        # Set up and connect socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(addr)

        # Grab established client logger
        self.client_logger = logging.getLogger('ClientLogger')

        # Send client information to server
        msg = 'INFO,{},{},{},{}\n'.format(self.id, self.chunksize, self.runtime, self.filesize)
        self.push(msg)

        # Set up dictionary used to lookup appropriate action based on incoming message
        self.msg_dict = {
            'START': self.start,
            'STOP': self.stop,
            'FILE_ROLL': self.report_file_roll
        }

    def handle_connect(self):
        self.is_connected = True
        self.heartbeat()

    def handle_close(self):
        self.is_connected = False
        self.close()

    def handle_expt(self):
        # connection failed, close socket
        self.handle_close()

    def collect_incoming_data(self, data):
        # Read incoming data and add to data buffer
        self.incoming.append(data)

    def found_terminator(self):
        # Interpret message from server
        msg = ''.join(self.incoming)
        self.incoming = []

    def heartbeat(self):
        # Send heartbeat message to server every 5 seconds
        print 'heartbeat'
        self.push('HEARTBEAT\n')
        if self.is_connected:
            thread = threading.Timer(5, self.heartbeat)
            thread.daemon = True
            thread.start()

    def start(self):
        if not self.check_size_vs_time():
            msg = 'INVALID configuration for client on port:{} detected. runtime specified ' \
                  'not long enough to roll file twice. Stopping client.'.format(self.addr[1])
            print msg
            self.client_logger.info(msg)
            self.stop()
            return
        self.push('START\n')
        msg = 'STARTED client on port:{}'.format(self.addr[1])
        self.client_logger.info(msg)
        # Setup and kick off data thread
        data_thread = threading.Thread(target=self.data_thread)
        data_thread.daemon = True
        data_thread.start()
        # Kick off data reporting thread
        threading.Timer(10, self.report_data).start()

    def stop(self):
        '''
        report stop to host
        stop all necessary threads gracefully
        '''
        self.push('STOP\n')
        msg = 'STOPPED client on port:{}'.format(self.addr[1])
        self.client_logger.info(msg)
        self.handle_close()

    def data_thread(self):
        # Open initial write file with unique name
        chunk = '0' * self.chunksize
        # Use temporary file to avoid flooding hard drive with files full of 0's
        f = tempfile.TemporaryFile()
        # To write actual files uncomment below and in while loop and import datetime
        '''filename = 'client_data-{}_'.format(self.addr[1]) \
                    + datetime.datetime.now().strftime('%H:%M:%S.%f_%B_%d_%Y')
        f = open(filename, 'w')'''
        start_time = time.time()
        # Write to this file until time is up. Handle file rolls as needed. Stop if socket becomes disconnected.
        while ((time.time() - start_time) < self.runtime) and self.is_connected:
            f.write(chunk)
            if (f.tell() + len(chunk)) >= self.filesize:
                # Write remainder of file then close and report file roll
                small_chunk = '0' * (self.filesize - f.tell())
                f.write(small_chunk)
                f.close()
                msg = 'Data file rolled for client on port:{}'.format(self.addr[1])
                self.client_logger.info(msg)
                self.report_file_roll()
                # Open new temporary file to continue writing
                f = tempfile.TemporaryFile()
                '''filename = 'client_data-{}_'.format(self.addr[1]) \
                            + datetime.datetime.now().strftime('%H:%M:%S.%f_%B_%d_%Y')
                f = open(filename, 'w')'''
        f.close()
        self.stop()

    def report_file_roll(self):
        #Simply report file roll to host
        self.push('FILE_ROLL\n')

    def report_data(self):
        # Report performance data to server every 10 seconds
        # Using random numbers as a proof of concept for now. Would use profiler on thread in full implementation.
        CPU = random.uniform(0,100)
        memory = random.uniform(0,100)
        print 'Sending performance data'
        if self.is_connected:
            thread = threading.Timer(10, self.report_data)
            thread.daemon = True
            thread.start()

    def check_size_vs_time(self):
        # Test time to write chunk then determine if given runtime is enough for 2 file rolls
        temp = tempfile.TemporaryFile()
        chunk = '0' * self.chunksize
        start = time.time()
        temp.write(chunk)
        end = time.time()
        time_per_chunk = end - start
        temp.close()
        if (float(self.filesize * time_per_chunk * 2) / self.chunksize) < self.runtime:
            return True
        else:
            return False


if __name__ == "__main__":
    # Set up socket to local host with arbitrary port
    host = socket.gethostname()
    port = 1989
    address = (host, port)

    # Set up client log (100Kbyte rotating log file for client start/stop and other messages)
    client_logger = logging.getLogger('ClientLogger')
    client_logger.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=12800, backupCount=1)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s  -  %(message)s')
    handler.setFormatter(formatter)
    client_logger.addHandler(handler)

    # Set up clients
    chunksize = 10 * 1024 * 1024 #10MiB
    runtime = 12
    filesize = 100 * chunksize #1000MiB
    id = 1

    first_client = BenchmarkClient(address, id, chunksize, runtime, filesize)
    # Couldn't get this error handling working
    '''except socket.error as err:
        if err.errno != errno.ECONNREFUSED:
            raise
        print 'Connection refused'
        msg = 'Client with id:{} refused'.format(id)
        client_logger.info(msg)'''

    # Kick off asyncore loop
    async_loop = threading.Thread(target=asyncore.loop)
    async_loop.daemon = True
    async_loop.start()


    first_client.start()
    while True:
        msg = raw_input('> ')
        if msg.lower() == 'quit':
            break
