# Distributed under MIT License
# Copyright (c) 2021 Remi BERTHOLET
""" Miscellaneous utility functions """
import sys
import os
import io
import time
import select
import hashlib
from binascii import hexlify

if sys.implementation.name == "micropython":
	def isKeyEnded(key):
		if len(key) == 0:
			return False
		elif len(key) == 1:
			if key == "\x1B":
				return False
			else:
				return True
		elif len(key) == 2:
			if key[0] == "\x1B" and key[1] == "\x1B":
				return False
			elif key[0] == "\x1B":
				if key[1] == "[" or key[1] == "(" or \
					key[1] == ")" or key[1] == "#" or \
					key[1] == "O":
					return False
				else:
					return True
		else:
			if ord(key[-1]) >= ord("A") and ord(key[-1]) <= ord("Z"):
				return True
			elif ord(key[-1]) >= ord("a") and ord(key[-1]) <= ord("z"):
				return True
			elif key[-1] == "~":
				return True
		return False

	_kbhit = False
	def getch(raw = True):
		global _kbhit
		key = ""
		_kbhit = False
		while 1:
			if len(key) == 0:
				delay = 1000000000
			else:
				delay = 0.01
			r,w,e = select.select([sys.stdin],[],[],delay)
			if isKeyEnded(key):
				if r != []:
					_kbhit = True
				break
			if r != []:
				char = sys.stdin.buffer.read(1)
				try:
					key += char.decode("latin-1")
				except:
					key +=  chr(ord(char))
			else:
				if len(key) > 0:
					break
		return key

	def kbhit():
		global _kbhit
		return _kbhit
else:
	def getch(raw = True):
		import termios, fcntl
		import select
		import os
		import sys
		import tty
		fd = sys.stdin.fileno()
		
		oldattr = termios.tcgetattr(fd)
		oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
		try:
			newattr = oldattr[:]
			newattr[3] = newattr[3] & ~termios.ICANON
			newattr[3] = newattr[3] & ~termios.ECHO
			termios.tcsetattr(fd, termios.TCSANOW, newattr)

			fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

			if raw:
				tty.setraw(fd)
			key = None
			inp, outp, err = select.select([sys.stdin], [], [])
			key = sys.stdin.read()
		finally:
			# Reset the terminal:
			fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
			termios.tcsetattr(fd, termios.TCSAFLUSH, oldattr)
		return key

	def kbhit():
		import sys
		import select
		inp, outp, err = select.select([sys.stdin], [], [], 0.001)
		if inp != []:
			return True
		return False

try:
	from utime import ticks_ms
	def ticks():
		return ticks_ms()
except:
	def ticks():
		import time
		return (int)(time.time() * 1000)

def ticksToString():
	""" Create a string with tick in seconds """
	tick = ticks()
	return "%d.%03d s"%(tick/1000, tick%1000)

previousTime = 0
def log(msg):
	""" Log line with a ticks displayed """
	current = ticks()
	global previousTime
	if previousTime == 0:
		previousTime = current
	print("%03d.%03d:%s"%((current-previousTime)/1000, (current-previousTime)%1000, msg))
	previousTime = ticks()

def dateToString(date = None):
	""" Get a string with the current date """
	return dateToBytes(date).decode("utf8")

def dateToBytes(date = None):
	""" Get a bytes with the current date """
	year,month,day,hour,minute,second,weekday,yearday = time.localtime(date)[:8]
	return b"%04d/%02d/%02d  %02d:%02d:%02d"%(year,month,day,hour,minute,second)

def dateToFilename(date = None):
	""" Get a filename with a date """
	filename = dateToString(date)
	filename = filename.replace("  ","_")
	filename = filename.replace("/","-")
	filename = filename.replace(":","-")
	return filename

def sizeToString(size, largeur=6):
	""" Convert a size in a string with k, m, g, t..."""
	return sizeToBytes(size, largeur).decode("utf8")

def sizeToBytes(size, largeur=6):
	""" Convert a size in a bytes with k, m, g, t..."""
	if size > 1073741824*1024:
		return  b"%*.2fT"%(largeur, size / (1073741824.*1024.))
	elif size > 1073741824:
		return  b"%*.2fG"%(largeur, size / 1073741824.)
	elif size > 1048576:
		return b"%*.2fM"%(largeur, size / 1048576.)
	elif size > 1024:
		return b"%*.2fK"%(largeur, size / 1024.)
	else:
		return b"%*dB"%(largeur, size)

def meminfo(display=True):
	""" Get memory informations """
	import gc
	try:
		alloc = gc.mem_alloc()
		free  = gc.mem_free()
		result = b"Mem alloc=%s free=%s total=%s"%(sizeToBytes(alloc, 1), sizeToBytes(free, 1), sizeToBytes(alloc+free, 1))
		if display:
			print(tostrings(result))
		else:
			return result
	except:
		return b"Mem unavailable"

def flashinfo(display=True):
	""" Get flash informations """
	try:
		import esp
		result = b"Flash user=%s size=%s"%(sizeToBytes(esp.flash_user_start(), 1), sizeToBytes(esp.flash_size(), 1))
		if display:
			print(tostrings(result))
		else:
			return result
	except:
		return b"Flash unavailable"

def sysinfo(display=True, text=""):
	""" Get system informations """
	try:
		import machine
		result = b"%s%s %dMhz, %s, %s, %s"%(text, sys.platform, machine.freq()//1000000, dateToBytes(), meminfo(False), flashinfo(False))
		if display:
			print(tostrings(result))
		else:
			return result
	except:
		return b"Sysinfo not available"

def splitext(p):
	""" Split file extension """
	sep='\\'
	altsep = '/'
	extsep = '.'
	sepIndex = p.rfind(sep)
	if altsep:
		altsepIndex = p.rfind(altsep)
		sepIndex = max(sepIndex, altsepIndex)

	dotIndex = p.rfind(extsep)
	if dotIndex > sepIndex:
		filenameIndex = sepIndex + 1
		while filenameIndex < dotIndex:
			if p[filenameIndex:filenameIndex+1] != extsep:
				return p[:dotIndex], p[dotIndex:]
			filenameIndex += 1
	return p, p[:0]

def split(p):
	""" Split file """
	sep = "/"
	i = p.rfind(sep) + 1
	head, tail = p[:i], p[i:]
	if head and head != sep*len(head):
		head = head.rstrip(sep)
	return head, tail

def import_(filename):
	""" Import filename """
	path, file = split(filename)
	moduleName, ext = splitext(file)

	if path not in sys.path:
		sys.path.append(path)

	try:
		del sys.modules[moduleName]
	except:
		pass
	try:
		module = exec("import %s"%moduleName)
		
		for fct in dir(sys.modules[moduleName]):
			if fct == "main":
				print("Start main function")
				sys.modules[moduleName].main()
				break
	except Exception as err:
		print(exception(err))
	except KeyboardInterrupt as err:
		print(exception(err))

def abspath(cwd, payload):
	""" Get the absolute path """
	# Just a few special cases "..", "." and ""
	# If payload start's with /, set cwd to /
	# and consider the remainder a relative path
	if payload.startswith('/'):
		cwd = "/"
	for token in payload.split("/"):
		if token == '..':
			if cwd != '/':
				cwd = '/'.join(cwd.split('/')[:-1])
				if cwd == '':
					cwd = '/'
		elif token != '.' and token != '':
			if cwd == '/':
				cwd += token
			else:
				cwd = cwd + '/' + token
	return cwd

def abspathbytes(cwd, payload):
	""" Get the absolute path into a bytes """
	# Just a few special cases "..", "." and ""
	# If payload start's with /, set cwd to /
	# and consider the remainder a relative path
	if payload.startswith(b'/'):
		cwd = b"/"
	for token in payload.split(b"/"):
		if token == b'..':
			if cwd != b'/':
				cwd = b'/'.join(cwd.split(b'/')[:-1])
				if cwd == b'':
					cwd = b'/'
		elif token != b'.' and token != b'':
			if cwd == b'/':
				cwd += token
			else:
				cwd = cwd + b'/' + token
	return cwd

def exists(filename):
	""" Test if the filename existing """
	try:
		rstat = os.lstat(filename)
		return True
	except:
		try:
			rstat = os.stat(filename)
			return True
		except:
			pass
	return False

previousFileInfo = []
def fileinfo(path):
	""" Get the file informations """
	global previousFileInfo
	if len(previousFileInfo) == 0:
		previousFileInfo = [path, os.stat(path)]
	elif previousFileInfo[0] != path:
		previousFileInfo = [path, os.stat(path)]
	return previousFileInfo[1]

def isdir(path):
	""" Indicates if the path is a directory """
	try:
		if fileinfo(path)[0] & 0x4000 == 0x4000:
			return True
	except:
		pass
	return False

def isfile(path):
	""" Indicates if the path is a file """
	try:
		if fileinfo(path)[0] & 0x4000 == 0:
			return True
	except:
		pass
	return False

def exception(err):
	""" Return the content of exception into a string """
	file = io.StringIO()
	if ismicropython():
		sys.print_exception(err, file)
		text = file.getvalue()
	else:
		try:
			import traceback
			file.write(traceback.format_exc())
		except Exception as err:
			print(err)
		text = file.getvalue()
		print(text)
	return text

def htmlException(err):
	""" Return the content of exception into an html bytes """
	text = exception(err)
	text = text.replace("\n    ","<br>&nbsp;&nbsp;&nbsp;&nbsp;")
	text = text.replace("\n  ","<br>&nbsp;&nbsp;")
	text = text.replace("\n","<br>")
	return tobytes(text)

def blink(duration=10):
	""" Blink led """
	try:
		import machine
		from time import sleep_ms
		pin2 = machine.Pin(2, machine.Pin.OUT)
		pin2.value(1)
		sleep_ms(duration)
		pin2.value(0)
		sleep_ms(duration)
	except:
		print("Blink")

def getScreenSize():
	""" Get the VT100 screen size """
	sys.stdout.write("\x1B[999;999f\x1B[6n")
	try:
		sys.stdout.flush()
	except:
		pass
	size = ""
	size = getch(False)
	size = size[2:-1].split(";")
	sys.stdout.write("\x1B[1000D")
	return int(size[0]), int(size[1])

def prefix(files):
	""" Get the common prefix of all files """
	# Initializes counters
	counters = []
	
	# For all files
	for file in files:
		# Split the file name into a piece
		paths = file.split("/")
		
		# For each piece
		for i in range(0,len(paths)):
			try:
				try:
					# Test if counters exist
					counters[i][paths[i]] += 1
				except:
					# Creates a path counters
					counters[i][paths[i]] = 1
			except:
				# Adds a new level of depth
				counters.append({paths[i] : 1})
	
	# Constructs the prefix of the list of files
	try:
		result = ""
		amount = list(counters[0].values())[0]
		for counter in counters:
			if len(counter.keys()) == 1 and list(counter.values())[0] == amount:
				result += list(counter.keys())[0] + "/"
			else:
				return result [:-1]
				break
		return result
	except IndexError:
		return ""

def getHash(password):
	""" Get the hash associated to the password """
	hash = hashlib.sha256()
	hash.update(password)
	return hexlify(hash.digest())

def now():
	""" Get time now """
	now = time.localtime()
	return now

def isascii(char):
	""" Indicates if the char is ascii """
	if len(char) == 1:
		if ord(char) >= 0x20 and ord(char) < 0x7F or char == "\t":
			return True
	return False

def isupper(char):
	""" Indicates if the char is upper """
	if len(char) == 1:
		if ord(char) >= 0x41 and ord(char) <= 0x5A:
			return True
	return False

def islower(char):
	""" Indicates if the char is lower """
	if len(char) == 1:
		if ord(char) >= 0x61 and ord(char) < 0x7A:
			return True
	return False

def isdigit(char):
	""" Indicates if the char is a digit """
	if len(char) == 1:
		if ord(char) >= 0x31 and ord(char) <= 0x39:
			return True
		return False

def isalpha(char):
	""" Indicates if the char is alpha """
	return isupper(char) or islower(char) or isdigit(char)

def isspace(char):
	""" Indicates if the char is a space, tabulation or new line """
	if char == " " or char == "\t" or char == "\n" or char == "\r":
		return True
	return False

def ispunctuation(char):
	""" Indicates if the char is a punctuation """
	if  (ord(char) >= 0x21 and ord(char) <= 0x2F) or \
		(ord(char) >= 0x3A and ord(char) <= 0x40) or \
		(ord(char) >= 0x5B and ord(char) <= 0x60) or \
		(ord(char) >= 0x7B and ord(char) <= 0x7E):
		return True
	else:
		return False

def dump(buff):
	""" Dump buffer """
	string = "\x1B[7m "
	for i in buff:
		if isascii(i):
			string += i
		else:
			string += "\\x%02x"%ord(i)
	string += " \x1B[m"
	return string

def makedir(directory, recursive=False):
	""" Make directory recursively """
	if recursive == False:
		os.mkdir(directory)
	else:
		directories = [directory]
		while 1:
			parts = split(directory)
			if parts[1] == "" or parts[0] == "":
				break
			directories.append(parts[0])
			directory = parts[0]

		directories.reverse()
		for d in directories:
			if not(exists(d)):
				os.mkdir(d)

def tobytes(datas, encoding="utf8"):
	""" Convert data to bytes """
	result = datas
	if type(datas) == type(""):
		result = datas.encode(encoding)
	elif type(datas) == type([]):
		result = []
		for item in datas:
			result.append(tobytes(item, encoding))
	elif type(datas) == type((0,0)):
		result = []
		for item in datas:
			result.append(tobytes(item, encoding))
		result = tuple(result)
	elif type(datas) == type({}):
		result = {}
		for key, value in datas.items():
			result[tobytes(key,encoding)] = tobytes(value, encoding)
	return result
	
def tostrings(datas, encoding="utf8"):
	""" Convert data to strings """
	result = datas
	if type(datas) == type(b""):
		result = datas.decode(encoding)
	elif type(datas) == type([]):
		result = []
		for item in datas:
			result.append(tostrings(item, encoding))
	elif type(datas) == type((0,0)):
		result = []
		for item in datas:
			result.append(tostrings(item, encoding))
		result = tuple(result)
	elif type(datas) == type({}):
		result = {}
		for key, value in datas.items():
			result[tostrings(key,encoding)] = tostrings(value, encoding)
	return result

def ismicropython():
	""" Indicates if the python is micropython """
	if sys.implementation.name == "micropython":
		return True
	return False

def iscamera():
	""" Indicates if the board is esp32cam """
	try:
		import camera 
		return camera.isavailable()
	except:
		if ismicropython():
			return False
		else:
			return True

def iptoint(ipaddr):
	""" Convert ip address into integer """
	spl = ipaddr.split(".")
	if len(spl):
		return ((int(spl[0])<<24)+ (int(spl[1])<<16) + (int(spl[2])<<8) + int(spl[3]))
	return 0

def issameinterface(ipaddr, ipinterface, maskinterface):
	""" indicates if the ip address is on the selected interface """
	ipaddr = iptoint(ipaddr)
	ipinterface  = iptoint(ipinterface)
	maskinterface = iptoint(maskinterface)
	if ipaddr & maskinterface == ipinterface & maskinterface:
		return True
	else:
		return False


def journalize(message):
	filename = tools.useful.dateToFilename()
	filename = "jnl_"+filename [8:-6] + ".txt"
	file = open(filename,"a")
	message = "%s: %s"%(tools.useful.dateToString(), message)
	print(message)
	file.write(message)
	file.write("\n")
	file.flush()
	file.close()
