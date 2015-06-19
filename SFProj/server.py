#!/usr/bin/env

import asynchat
import asyncore
import socket
import threading
import logging, logging.handlers
import sqlite3
import datetime

LOG_FILENAME = 'server_log.log'

class ClientHandler(asynchat.async_chat):
    # Each client's handler is set up to receive and respond appropriately to messages
    # sent from the client at any time.

    def __init__(self, sock, addr, database):
        asynchat.async_chat.__init__(self, sock=sock)
        self.addr = addr
        self.database = database
        self.set_terminator('\n')
        self.incoming = [] # Buffer for incoming messages from client
        self.current_msg = None
        self.started = False
        self.stopped = False
        self.id = None
        self.chunksize = None
        self.runtime = None
        self.filesize = None
        self.filerolls = 0
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
        # Handle message from client
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
        # Connection failed, close socket
        self.handle_close()

    def handle_client_info(self):
        # Set client info in handler based on info from client
        info_list = self.current_msg.split(',')
        self.id = int(info_list[1])
        self.chunksize = int(info_list[2])
        self.runtime = int(info_list[3])
        self.filesize = int(info_list[4])
        # Add client entry to database
        self.database.add_new_client(self.id)

    def handle_heartbeat(self):
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
        self.filerolls += 1
        msg = 'Data file rolled on client id:{} on port:{}'.format(self.id, self.addr[1])
        self.server_logger.info(msg)

    def handle_perfdata(self):
        # Get performance data from client and update client database entry
        perf_data = self.current_msg.split(',')
        cpu = float(perf_data[1])
        memory = float(perf_data[2])
        # Store in db
        self.database.update_data(self.id, cpu, memory)


class BenchmarkServer(asyncore.dispatcher):
    # The benchmark server uses Python's asynchronous infrastructure to interface with multiple clients.
    # Messages are used to communicate between the server and its clients through each client's handler.

    def __init__(self, address, database):
        asyncore.dispatcher.__init__(self)
        # Create and bind socket for server
        self.database = database
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
                print 'Beginning benchmark session...'
                report_thread = threading.Timer(10, self.check_report)
                report_thread.daemon = True
                report_thread.start()
            self.clients.append(ClientHandler(sock, addr, self.database))

    def check_report(self):
        # If all clients have been both started and stopped, write report
        for client in self.clients:
            if not client.started or not client.stopped:
                report_thread = threading.Timer(10, self.check_report)
                report_thread.daemon = True
                report_thread.start()
                return
        self.generate_report()

    def generate_report(self):
        print 'Generating report...'
        filename = 'server_report_' + datetime.datetime.now().strftime('%H:%M:%S_%B_%d_%Y')
        f = open(filename, 'w')
        line = 'Server report created on ' + datetime.datetime.now().strftime('%B %d %Y %H:%M:%S') + '\n'
        f.write(line)
        line = 'Benchmark server ran with {} clients\n\n'.format(len(self.clients))
        f.write(line)
        for client in self.clients:
            cpu = self.database.get_cpu(client.id)
            mem = self.database.get_mem(client.id)
            line = 'Client id: {}, General usage:\n' \
                   '   Run duration = {}\n' \
                   '   File size    = {}\n' \
                   '   Chunk size   = {}\n' \
                   '   File rolls   = {}\n' \
                   ''.format(client.id, client.runtime, client.filesize, client.chunksize, client.filerolls)
            f.write(line)
            line = 'Performance data:\n' \
                   '   CPU Performance    = {}\n' \
                   '   Memory Performance = {}\n\n' \
                   ''.format(cpu, mem)
            f.write(line)
        f.close()
        # Clear out clients list to allow for next test session (run client.py again)
        self.clients = []


class PerfDB(object):
    # This is a wrapper object used to simply calls to the SQLite database that holds performance data

    def __init__(self):
        # Set up SQLite database for storing client performance data
        self.connection = sqlite3.connect('client_performance.db', check_same_thread=False)
        self.cursor = self.connection.cursor()
        init = '''CREATE TABLE if not exists PerfData (
                        client_id INTEGER PRIMARY KEY,
                        cpu REAL,
                        mem REAL)'''
        self.cursor.execute(init)

    def gen_query(self, query):
        return self.cursor.execute(query)

    def add_new_client(self, client_id):
        self.cursor.execute("INSERT OR REPLACE INTO PerfData VALUES(?, 0, 0)", (client_id,))

    def update_data(self, client_id, cpu, mem):
        # Update cpu and memory performance data for specified client
        self.cursor.execute("UPDATE PerfData SET cpu=? WHERE client_id=?", (cpu, client_id))
        self.cursor.execute("UPDATE PerfData SET mem=? WHERE client_id=?", (mem, client_id))

    def get_cpu(self, client_id):
        # Grab cpu performance data for specified client
        self.cursor.execute("SELECT cpu FROM PerfData WHERE client_id=?", (client_id,))
        cpu = self.cursor.fetchone()[0]
        return cpu

    def get_mem(self, client_id):
        # Grab memory performance data for specified client
        self.cursor.execute("SELECT mem FROM PerfData WHERE client_id=?", (client_id,))
        mem = self.cursor.fetchone()[0]
        return mem

    def __del__(self):
        # Clean up
        self.connection.close()


if __name__ == "__main__":
    # Create SQLite database object to pass to server
    perf_db = PerfDB()

    # Set up local server on arbitrary port
    host = socket.gethostname()
    port = 1989
    server = BenchmarkServer((host, port), perf_db)

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