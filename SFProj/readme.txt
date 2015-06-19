SolidFire Benchmarking Tool Exercise
By Wade Pentz

Instructions for usage:
1. Setup clients in '__main__' function in client.py.
2. Run server.py
3. Run client.py
4. Keyboard interrupt to close server, client will close itself when done.

NOTE: The server is set up to run forever and will accept multiple consecutive client sessions.

Limitations:
1. The check to determine if the file will roll twice within the allotted time is not as accurate as it could be.
   The check is done before all of the client threads have been kicked off and so the demand on the system is less
   when the time measurement is taken.
2. Clients will each send out one extra heartbeat and one extra set of performance data after they are closed due to an
   open timed thread. These will not, however, be sent to the server because the BenchmarkClient's socket will be closed.
3. The server will occasionally not receive the start/stop messages from clients. If this occurs a server reset is
   required. The asyncore/asynchat service seems to drop messages sent by clients occasionally.
4. Currently client performance data is generated using a random number generator. It may be possible to use Python's
   standard profilers to get actual performance data.
5. The current server does not log when clients when away.

Future Improvements:
1. Properly clear client list on server side so that clients that go offline are removed.
2. Overall robustness improvements, including but not limited to:
   - Error handling
   - Improved thread safety and clean-up
3. Expand SQLite database functionality to store additional data points.
4. Client config file that is read by client to accommodate client set up outside of code.
5. Implement Flask web server to host GUI for managing server/clients.
6. Fix bugs & missing features listed in 'Limitations'.
7. Use Twisted framework instead of asyncore and asynchat to implement asynchronous server. This would improve the
   robustness of the server especially in terms of threading. The database had to be setup with check_same_thread=False
   to accommodate inherent threading in asyncore infrastructure.


