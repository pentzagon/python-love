#!/usr/bin/env

import asynchat
import asyncore
import socket
import threading
import logging, logging.handlers

LOG_FILENAME = 'server_log.log'
# Bank of client info
#clients = []

class ClientHandler(asynchat.async_chat):
    # Each client's handler is set up to receive and respond appropriately to messages
    # sent from the client at any time.

    def __init__(self, sock, addr):
        asynchat.async_chat.__init__(self, sock=sock)
        self.addr = addr
        self.set_terminator('\n')
        self.incoming = [] # Buffer for incoming messages from client
        self.current_msg = None
        self.started = False
        self.stopped = False
        self.id = None
        self.chunksize = None
        self.runtime = None
        self.filesize = None
        # Set up dictionary used to lookup appropriate action based on incoming message
        self.cmd_dict = {
            'INFO': self.handle_client_info,
            'HEARTBEAT': self.handle_heartbeat,
            'START': self.handle_start,
            'STOP': self.handle_stop,
            'FILE_ROLL': self.handle_fileroll,
            'PERF_DATA': self.handle_perfdata
        }
        self.server_logger = logging.getLogger('ServerLogger')

    def collect_incoming_data(self, data):
        # Read incoming data and add to incoming data buffer
        self.incoming.append(data)

    def found_terminator(self):
        self.current_msg = ''.join(self.incoming)
        cmd = self.current_msg.split(',')[0]
        print cmd
        # Respond to message from client
        try:
            self.cmd_dict[cmd]()
        except KeyError:
            msg = 'Invalid client message received from port:{}'.format(self.addr[1])
            print msg
            self.server_logger.info(msg)

        self.incoming = []

    def handle_close(self):
        self.close()

    def handle_expt(self):
        # connection failed, close socket
        self.handle_close()

    def handle_client_info(self):
        info_list = self.current_msg.split(',')
        self.id = int(info_list[1])
        self.chunksize = int(info_list[2])
        self.runtime = int(info_list[3])
        self.filesize = int(info_list[4])
        print 'self.id={}, self.chunksize={}, self.runtime={}, ' \
              'self.filesize={}'.format(self.id, self.chunksize, self.runtime, self.filesize)

    def handle_heartbeat(self):
        #print 'Heartbeat received from port:{}'.format(self.addr[1])
        msg = 'Heartbeat from client id:{} on port:{}'.format(self.id, self.addr[1])
        self.server_logger.info(msg)

    def handle_start(self):
        self.started = True
        msg = 'STARTED client id:{} on port:{}'.format(self.id, self.addr[1])
        self.server_logger.info(msg)

    def handle_stop(self):
        self.stopped = True
        msg = 'STOPPED client id:{} on port:{}'.format(self.id, self.addr[1])
        self.server_logger.info(msg)

    def handle_fileroll(self):
        msg = 'Data file rolled on client id:{} on port:{}'.format(self.id, self.addr[1])
        self.server_logger.info(msg)

    def handle_perfdata(self):
        pass

class BenchmarkServer(asyncore.dispatcher):
    # The benchmark server uses Python's asynchronous infrastructure to interface with multiple clients.
    # Messages are used to communicate between the server and its clients through each client's handler.

    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        # Create and bind socket for server
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        # Allow up to 5 client connections
        self.listen(5)
        # Keep bank of connected clients
        self.clients = []
        # Set up server log (100Kbyte rotating log file for client heartbeat and other messages)
        self.server_logger = logging.getLogger('ServerLogger')
        self.server_logger.setLevel(logging.INFO)
        handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=12800, backupCount=1)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s  -  %(message)s')
        handler.setFormatter(formatter)
        self.server_logger.addHandler(handler)

    def handle_accept(self):
        client_info = self.accept()
        # Give new client to ClientHandler and add to client list
        if client_info is not None:
            sock, addr = client_info
            print 'Incoming connection from {}'.format(addr)
            # If this is the first client connected set up polling loop to wait for all clients to finish for report
            if not self.clients:
                report_thread = threading.Timer(5, self.check_report)
                report_thread.daemon = True
                report_thread.start()
            self.clients.append(ClientHandler(sock, addr))

    def check_report(self):
        # If all clients have been both started and stopped, write report
        for client in self.clients:
            if not client.started or not client.stopped:
                report_thread = threading.Timer(5, self.check_report)
                report_thread.daemon = True
                report_thread.start()
                return
        self.generate_report()

    def generate_report(self):
        print 'Generating report...'
        '''for client in self.clients:
            pass
            clear client off of list'''

if __name__ == "__main__":
    # Set up local server on arbitrary port
    host = socket.gethostname()
    port = 1989
    server = BenchmarkServer((host, port))

    try:
        # Activate server
        activation_msg = 'Now serving clients on {}:{}'.format(host, port)
        print activation_msg
        server.server_logger.info(activation_msg)
        asyncore.loop()
        '''async_loop = threading.Thread(target=asyncore.loop)
        async_loop.daemon = True
        async_loop.start()'''
    except KeyboardInterrupt:
        close_msg = 'Closing server...'
        print close_msg
        server.server_logger.info(close_msg)
        server.handle_close()