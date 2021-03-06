# Distributed under MIT License
# Copyright (c) 2021 Remi BERTHOLET
""" Classes used to manage the wifi station """
import sys
from tools import jsonconfig
from tools import useful

class StationConfig:
	""" Wifi station configuration class """
	def __init__(self):
		""" Constructor """
		self.activated     = True
		self.wifipassword  = b""
		self.ssid          = b""
		self.ipaddress     = b""
		self.netmask       = b""
		self.gateway       = b""
		self.dns           = b""

	def __repr__(self):
		""" Display the content of wifi station """
		# Get network address
		ipaddress, netmask, gateway, dns = Station.wlan.ifconfig()

		result = "%s:\n"%self.__class__.__name__
		result +="   Ip address :%s\n"%ipaddress
		result +="   Netmask    :%s\n"%netmask
		result +="   Gateway    :%s\n"%gateway
		result +="   Dns        :%s\n"%dns
		result +="   Ssid       :%s\n"%useful.tostrings(self.ssid)
		# result +="   Password   :%s\n"%useful.tostrings(self.wifipassword)
		result +="   Activated  :%s\n"%useful.tostrings(self.activated)
		return result

	def save(self, file = None):
		""" Save wifi configuration """
		result = jsonconfig.save(self, file)
		return result

	def update(self, params):
		""" Update wifi configuration """
		result = jsonconfig.update(self, params)
		return result

	def load(self, file = None):
		""" Load wifi configuration """
		result = jsonconfig.load(self, file)
		return result

class Station:
	""" Class to manage wifi station """
	wlan = None
	config = None
	networks  = []

	@staticmethod
	def connect(ssid=None, password=None):
		""" Connect to wifi hotspot """
		result = False
		if ssid     != None: Station.config.ssid     = ssid
		if password != None: Station.config.wifipassword = password
		if not Station.wlan.isconnected():
			Station.wlan.active(True)
			Station.wlan.connect(useful.tobytes(Station.config.ssid), useful.tobytes(Station.config.wifipassword))
			from time import sleep
			count = 0
			while not Station.wlan.isconnected():
				sleep(0.5)
				
				if count % 6 == 0:
					print ("Try wifi connection")
				count += 1
				if count > 120:
					break
				
			
			if Station.wlan.isconnected() == False:
				Station.wlan.active(False)
			else:
				result = True
		else:
			result = True
		return result

	@staticmethod
	def disconnect(self):
		""" Disconnect the wifi """
		if Station.wlan.isconnected():
			Station.wlan.disconnect()
			Station.wlan.active(False)
	
	@staticmethod
	def isActive():
		""" Indicates if the wifi is active """
		if Station.wlan == None:
			return False
		return Station.wlan.active()

	@staticmethod
	def configure(ipaddress = None, netmask = None, gateway = None, dns = None):
		""" Configure the wifi """
		if ipaddress != None: Station.config.ipaddress = useful.tobytes(ipaddress)
		if netmask   != None: Station.config.netmask   = useful.tobytes(netmask)
		if gateway   != None: Station.config.gateway   = useful.tobytes(gateway)
		if dns       != None: Station.config.dns       = useful.tobytes(dns)

		if Station.config.ipaddress == b"": Station.config.ipaddress = useful.tobytes(Station.wlan.ifconfig()[0])
		if Station.config.netmask   == b"": Station.config.netmask   = useful.tobytes(Station.wlan.ifconfig()[1])
		if Station.config.gateway   == b"": Station.config.gateway   = useful.tobytes(Station.wlan.ifconfig()[2])
		if Station.config.dns       == b"": Station.config.dns       = useful.tobytes(Station.wlan.ifconfig()[3])

		if Station.config.ipaddress == b"0.0.0.0": Station.config.ipaddress = b""
		if Station.config.netmask   == b"0.0.0.0": Station.config.netmask   = b""
		if Station.config.gateway   == b"0.0.0.0": Station.config.gateway   = b""
		if Station.config.dns       == b"0.0.0.0": Station.config.dns       = b""

		try:
			if Station.config.ipaddress != b"" and \
				Station.config.netmask   != b"" and \
				Station.config.gateway   != b"" and \
				Station.config.dns       != b"":
				Station.wlan.ifconfig((
					useful.tostrings(Station.config.ipaddress),
					useful.tostrings(Station.config.netmask),
					useful.tostrings(Station.config.gateway),
					useful.tostrings(Station.config.dns)))
		except Exception as err:
			print("Cannot configure wifi station %s"%useful.exception(err))

	@staticmethod
	def getInfo():
		if Station.wlan != None and Station.wlan.isconnected():
			return Station.wlan.ifconfig()
		return None

	@staticmethod
	def isConnected():
		""" Indicates if the wifi is connected """
		return Station.wlan.isconnected()

	@staticmethod
	def scan(force=False):
		""" Scan all wifi networks """
		if force == True or len(Station.networks) == 0:
			Station.networks = []
			networks = Station.wlan.scan()
			for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
				Station.networks.append((ssid, channel, authmode))
		return Station.networks

	@staticmethod
	def start(force):
		""" Start the wifi according to the configuration. Force is used to skip configuration activation flag """
		result = False
		if Station.isActive() == False:
			config = StationConfig()
			if config.load():
				if config.activated or force:
					from network import WLAN, STA_IF
					Station.wlan = WLAN(STA_IF)
					Station.config = config
					Station.networks  = []
					print("Start wifi")
					Station.configure()
					if Station.connect():
						print(repr(Station.config))
					else:
						print("Wifi connection failed")
					result = True
				else:
					print("Wifi disabled")
			else:
				print("Wifi not initialized")
		else:
			print("Wifi already started")
			print(repr(Station.config))
			result = True
		return result

	@staticmethod
	def stop():
		""" Stop the wifi station """
		if Station.isActive() == False:
			print("Wifi stopped")

	@staticmethod
	def isIpOnInterface(ipAddr):
		""" Indicates if the address ip is connected to wifi station """
		ipInterface = Station.getInfo()
		if ipInterface != None:
			return useful.issameinterface(useful.tostrings(ipAddr), ipInterface[0], ipInterface[1])
		return False