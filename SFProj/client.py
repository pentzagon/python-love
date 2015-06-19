#!/usr/bin/env

import asynchat
import asyncore
import socket
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
        self.is_connected = False

        # Grab established client logger
        self.client_logger = logging.getLogger('ClientLogger')

        # Check if set time is long enough for data file to roll over twice
        if not self.check_size_vs_time():
            msg = 'INVALID configuration for client id:{} detected. runtime specified ' \
                  'not long enough to roll file twice. Stopping client.'.format(self.id)
            print msg
            self.client_logger.info(msg)
            self.stop()
            raise ValueError

        # Set up and connect socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(addr)


        # Send client information to server
        msg = 'INFO,{},{},{},{}\n'.format(self.id, self.chunksize, self.runtime, self.filesize)
        self.push(msg)

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
        self.push('HEARTBEAT\n')
        if self.is_connected:
            thread = threading.Timer(5, self.heartbeat)
            thread.daemon = True
            thread.start()

    def start(self):
        self.push('START\n')
        msg = 'STARTED client id:{}'.format(self.id)
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
        msg = 'STOPPED client id:{}'.format(self.id)
        self.client_logger.info(msg)
        self.handle_close()

    def data_thread(self):
        # Open initial write file with unique name
        chunk = '0' * self.chunksize
        start_time = time.time()
        # Spooled temp files will write a temporary file to disk when the file rolls over.
        # This simulates an actual disk write without flooding the hard drive with files full of 0's.
        f = tempfile.SpooledTemporaryFile(max_size=self.filesize)
        # Write to this file until time is up. Handle file rolls as needed. Stop if socket becomes disconnected.
        while ((time.time() - start_time) < self.runtime) and self.is_connected:
            f.write(chunk)
            if f._rolled == True:
                f.close()
                self.report_file_roll()
                f = tempfile.SpooledTemporaryFile(max_size=self.filesize)
        f.close()
        self.stop()

    def check_size_vs_time(self):
        # Throw error if runtime is less than 10 seconds since no performance data will be reported in this case
        if self.runtime < 10:
            return False
        # Test time to write file and force file rollover then determine if given runtime is enough for 2 file rolls
        temp = tempfile.SpooledTemporaryFile(max_size=(self.filesize))
        chunk = '0' * self.chunksize
        start = time.time()
        while temp._rolled == False:
            temp.write(chunk)
        temp.close()
        # This method is called before the client is connected so this file roll will not be logged to the server
        self.report_file_roll()
        end = time.time()
        time_per_file_roll = end - start
        print 'client:{} - time_per_file_roll={}'.format(self.id, time_per_file_roll)
        temp.close()
        if (time_per_file_roll * 2) < self.runtime:
            print 'client:{} OKAY'.format(self.id)
            return True
        else:
            print 'client:{} ERROR - Invalid configuration'.format(self.id)
            return False

    def report_file_roll(self):
        # Simply report file roll to host
        self.push('FILE_ROLL\n')
        msg = 'File rolled on client id:{}'.format(self.id)
        self.client_logger.info(msg)

    def report_data(self):
        # Report performance data to server every 10 seconds
        # Using random numbers as a proof of concept for now. Would use profiler in full implementation.
        CPU = random.uniform(0,100)
        memory = random.uniform(0,100)
        msg = 'PERF_DATA,{},{}\n'.format(CPU, memory)
        self.push(msg)
        if self.is_connected:
            thread = threading.Timer(10, self.report_data)
            thread.daemon = True
            thread.start()


if __name__ == "__main__":
    # Set up socket to local host with arbitrary port
    host = socket.gethostname()
    port = 1989
    address = (host, port)
    clients = []

    # Set up client log (100Kbyte rotating log file for client start/stop and other messages)
    client_logger = logging.getLogger('ClientLogger')
    client_logger.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=12800, backupCount=1)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s  -  %(message)s')
    handler.setFormatter(formatter)
    client_logger.addHandler(handler)

    print 'Creating and checking clients...'
    # SET UP CLIENTS HERE
    # These clients are currently set up in a configuration that successfully completes as a test case on my PC.
    # If performance on the test computer is poor they Modify as you see fit :-)
    chunksize = 10 * 1024 * 1024 #10MiB
    runtime = 32 #seconds
    filesize = 1000 * 1024 * 1024 #1000MiB
    id = 1
    first_client = BenchmarkClient(address, id, chunksize, runtime, filesize)
    clients.append(first_client)

    chunksize = 20 * 1024 * 1024 #20MiB
    runtime = 27
    filesize = 500 * 1024 * 1024 #500MiB
    id = 2
    second_client = BenchmarkClient(address, id, chunksize, runtime, filesize)
    clients.append(second_client)

    chunksize = 30 * 1024 * 1024 #30MiB
    runtime = 34
    filesize = 250 * 1024 * 1024 #250MiB
    id = 3
    third_client = BenchmarkClient(address, id, chunksize, runtime, filesize)
    clients.append(third_client)

    chunksize = 80 * 1024 * 1024 #80MiB
    runtime = 29
    filesize = 750 * 1024 * 1024 #750MiB
    id = 4
    fourth_client = BenchmarkClient(address, id, chunksize, runtime, filesize)
    clients.append(fourth_client)

    chunksize = 15 * 1024 * 1024 #15MiB
    runtime = 34
    filesize = 100 * 1024 * 1024 #100MiB
    id = 5
    fifth_client = BenchmarkClient(address, id, chunksize, runtime, filesize)
    clients.append(fifth_client)

    # Kick off asyncore loop
    async_loop = threading.Thread(target=asyncore.loop)
    async_loop.daemon = True
    async_loop.start()

    # Start all clients (stagger for interesting timing)
    print 'Starting all clients...'
    first_client.start()
    time.sleep(1)
    second_client.start()
    time.sleep(1)
    third_client.start()
    fourth_client.start()
    time.sleep(2)
    fifth_client.start()

    print

    # Loop until all clients are disconnected then quit
    while True:
        if any(client.connected for client in clients):
            continue
        else:
            print 'Client session complete!'
            quit()
