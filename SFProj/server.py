#!/usr/bin/env

import asynchat
import asyncore
import socket
import logging

clients = {}

class ClientHandler(asynchat.async_chat):

    def __init__(self, sock, addr):
        asynchat.async_chat.__init__(self, sock=sock, map=clients)
        self.addr = addr
        self.set_terminator('\n')
        self.incoming = []
        # Set up dictionary reference response to incoming messages
        self.msg_dict = {
            'HEARTBEAT': self.recv_heartbeat
        }

    def collect_incoming_data(self, data):
        # Read incoming data and add to incoming data buffer
        self.incoming.append(data)

    def found_terminator(self):
        msg = ''.join(self.incoming)
        # print 'Received: ', msg
        # Respond to message from client
        try:
            self.msg_dict[msg]()
        except KeyError:
            print 'Invalid client message received from port:{}'.format(self.addr[1])
        self.incoming = []

    def recv_heartbeat(self):
        print 'Heartbeat received from port:{}'.format(self.addr[1])


class BenchmarkServer(asyncore.dispatcher):

    def __init__(self, address):
        asyncore.dispatcher.__init__(self, map=clients)
        # Create and bind socket for server
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        #self.address = self.socket.getsockname()
        self.listen(5)

    def handle_accept(self):
        client_info = self.accept()
        if client_info is not None:
            sock, addr = client_info
            print 'Incoming connection from {}'.format(addr)
            handler = ClientHandler(sock, addr)

    def handle_close(self):
        self.close()

if __name__ == "__main__":
    # Set up local server on arbitrary port
    host = socket.gethostname()
    port = 1989
    server = BenchmarkServer((host, port))

    try:
        # Activate server
        print 'Now serving clients on {}:{}'.format(host, port)
        asyncore.loop(map=clients)
    except KeyboardInterrupt:
        print 'Closing server...'
        server.close()