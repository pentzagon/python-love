#!/usr/bin/env

import asynchat
import asyncore
import socket
import threading
import time
import logging

class BenchmarkClient(asynchat.async_chat):

    def __init__(self, address):
        asynchat.async_chat.__init__(self)
        self.address = address
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(address)
        self.set_terminator('\n')
        self.incoming = []

    def handle_connect(self):
        self.heartbeat()

    def collect_incoming_data(self, data):
        # Read incoming data and add to data buffer
        self.incoming.append(data)

    def found_terminator(self):
        # Interpret message from server
        msg = ''.join(self.incoming)
        print 'Received: ', msg
        self.incoming = []

    def heartbeat(self):
        msg = 'HEARTBEAT\n'
        self.push(msg)
        threading.Timer(5, self.heartbeat).start()

if __name__ == "__main__":
    # Set up socket to local host with arbitrary port
    host = socket.gethostname()
    port = 1989
    address = (host, port)

    # Set up clients
    first_client = BenchmarkClient(address)
    # asyncore.loop()
    comm_loop = threading.Thread(target=asyncore.loop)
    comm_loop.daemon = True
    comm_loop.start()

    while True:
        msg = raw_input('> ')
        first_client.push(msg + '\n')

