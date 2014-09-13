import socket
import sys
import select
from Connect import Connect

HTTP_PORT = 80
HOST = "" # default; any address
arbitrary_port = 9999 # default, should be changed on execution
MAX_CONNECTIONS = 200
BUFFER_SIZE = 4096
DEFAULT_FORWARD_HOST = "www.google.com" # temporary

class MyProxy:

	inputs = [] # stores all the avaiable sockets
	channel = {} # dictionary for associating endpoints: client-server

	def __init__(self, host, port):
		try:
			# creates an AF_INET (IPv4), STREAM socket (TCP)
			self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server.bind((host, port))
			self.server.listen(MAX_CONNECTIONS)
			print "Successfully created server, listening for connections..."
		except socket.error, msg:
			print "Failed to create socket! Error code: " + str(msg[0]) + " , Error message: " + msg[1]
			sys.exit(1);


	def main_loop(self):
		self.inputs.append(self.server) # first available socket is server itself
		while 1:
			inputs_ready, outputs_ready, except_ready = select.select(self.inputs, [], [])
			for self.socket in inputs_ready:
				if self.socket == self.server:
					self.trigger_accept()
					break

				self.data = self.socket.recv(BUFFER_SIZE)
				if len(self.data) == 0:
					self.trigger_close()
				else:
					self.trigger_recv()


	def trigger_accept(self):
		connection = Connect().start(DEFAULT_FORWARD_HOST, HTTP_PORT)
		client_socket, client_addr = self.server.accept()
		if connection:
			print "New connection established with: ", client_addr
			self.inputs.append(client_socket)
			self.inputs.append(connection)
			self.channel[client_socket] = connection
			self.channel[connection] = client_socket
		else:
			print "Cannot establish connection with remote server.",
			print "Closing connection with client: ", client_addr
			client_socket.close()


	def trigger_close(self):
		print self.socket.getpeername(), " has disconnected"
		self.inputs.remove(self.socket)
		self.inputs.remove(self.channel[self.socket])
		out = self.channel[self.socket]
		self.channel[out].close() 
		self.channel[self.socket].close()
		del self.channel[out]
		del self.channel[self.socket]


	def trigger_recv(self):
		data = self.data
		# parsing goes here
		print data
		self.channel[self.socket].send(data)


if __name__ == "__main__":
	try:
		arbitrary_port = int(raw_input("Arbitrary port for a proxy server: "))
		myProxy = MyProxy(HOST, arbitrary_port)
	except ValueError, e:
		print arbitrary_port, " is not a valid integer!"
		sys.exit(1);
	
	try:
		myProxy.main_loop()
	except KeyboardInterrupt:
		print " ---> Caught SIGINT. Stopping server..."
		sys.exit(1)
