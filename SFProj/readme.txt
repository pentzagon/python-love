SolidFire Benchmarking Tool Exercise
By Wade Pentz

Instructions for usage:
1. Setup clients in '__main__' function in client.py.
2. Run server.py
3. Run client.py
4. Keyboard interrupt on both when done

NOTE: If the clients error out upon start up due to problems with invalid client configurations the server will also
      need to be reset. This is due to the client list on the server side not being depopulated correctly.

Limitations:
1. The check to determine if the file will roll twice within the allotted time is not as accurate as it should be.
   Currently it writes a temp file
2. Clients will each send out one extra heartbeat and one extra performance data after they are closed due to an open
   timed thread. These will not, however, be sent to the server because the BenchmarkClient's socket will be closed.
3. Currently the clients write temporary files

Future Improvements:
1. Use Twisted framework instead of asyncore and asynchat to implement asynchronous server. This would improve the
   robustness of the server especially in terms of threading. The database had to be setup with check_same_thread=False
   to accommodate inherent threading in asyncore infrastructure. This framework was not used due to the perceived learning
   curve. I did not want to cludge together a server with Twisted without understanding the underlying framework.
2. Properly clear client list on server side so that clients that go offline are removed.
3. Overall robustness improvements, including but not limited to:
   - Error handling
   - Improved thread safety and clean-up
4. Client config file that is read by client to accommodate custom client set up
5. Flask web server to host GUI for managing server/clients.


