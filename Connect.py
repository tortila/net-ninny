import socket

class Connect:
	def __init__(self):
		self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def start(self, host, port):
		try:
			self.connection.connect((host, port))
			return self.connection
		except Exception, e:
			print e
			return False