#!/usr/bin/env

import SocketServer
import threading
import socket

class ClientRequestHandler(SocketServer.StreamRequestHandler):
    # This class is instantiated when a request is received from a client

    def handle(self):
        self.data = self.request.recv(1024)
        # Add client to server client_list
        self.server.client_list.append(self.request)
        print self.server.client_list
        while True:
            # Echo message back to the client
            print 'Return message to client'
            self.request.send(self.data.upper())
        return

class BenchmarkServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True

    def __init__(self, server_address, handler_class):
        # Set up client list to keep track of clients
        self.client_list = []
        SocketServer.TCPServer.__init__(self, server_address, handler_class)
        return


if __name__ == "__main__":
    # Set up local TCP server on arbitrary port
    host = socket.gethostname()
    port = 1989
    address = (host, port)
    server = BenchmarkServer(address, ClientRequestHandler)

    # Activate server
    print 'Now serving TCP clients...'
    server.serve_forever()