#!/usr/bin/env

import socket
import threading
import time

class BenchmarkClient:

    def __init__(self, address):
        self.address = address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(address)

def setup_client():
    pass

if __name__ == "__main__":
    # Set up socket to local host with arbitrary port
    host = socket.gethostname()
    port = 1989
    address = (host, port)

    # Set up 1st client
    first_client = BenchmarkClient(address)

    message1 = 'Client 1 request'
    message_length = first_client.socket.send(message1)
    server_message = first_client.socket.recv(message_length)
    print server_message
    message_length = first_client.socket.send(message1)
    server_message = first_client.socket.recv(message_length)
    print server_message
    message_length = first_client.socket.send(message1)
    server_message = first_client.socket.recv(message_length)
    print server_message

    """
    # Set up 1st client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(address)
    message1 = 'Client 1 request'
    message_length = client_socket.send(message1)
    server_message = client_socket.recv(message_length)
    print server_message
    message1 = 'Client 1 request again'
    message_length = client_socket.send(message1)
    server_message = client_socket.recv(message_length)
    print server_message

    # Set up 2nd client
    client_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket2.connect(address)
    message2 = 'Client 2 connected'
    message_length2 = client_socket2.send(message2)
    print client_socket2.recv(message_length2)

    client_socket.close()
    client_socket2.close()
    """

