# -*- Mode: Python; tab-width: 4 -*-

#			
# medusa status extension
#

import string
import time
import regex

import asyncore
import http_server
import medusa_gif
import producers
from counter import counter

START_TIME = long(time.time())

# split a uri
# <path>;<params>?<query>#<fragment>
path_regex = regex.compile (
#        path        params        query       fragment
	'\\([^;?#]*\\)\\(;[^?#]*\\)?\\(\\?[^#]*\)?\(#.*\)?'
	)

def split_path (path):
	if path_regex.match (path) != len(path):
		raise ValueError, "bad path"
	else:
		return map (lambda i,r=path_regex: r.group(i), range(1,5))

class status_extension:
	hit_counter = counter()

	hyper_regex = regex.compile ('/status/object/\([0-9]+\)/.*')

	def __init__ (self, objects, regexp='/status\(/.*\)?'):
		self.objects = objects
		self.regexp = regex.compile (regexp)
		self.hyper_objects = []
		for object in objects:
			self.register_hyper_object (object)

	def __repr__ (self):
		return '<Status Extension (%s hits) at %x>' % (
			self.hit_counter,
			id(self)
			)

	def match (self, request):
		[path, params, query, fragment] = split_path (request.uri)
		return self.regexp.match (path) == len(path)

	# Possible Targets:
	# /status
	# /status/channel_list
	# /status/medusa.gif

	# can we have 'clickable' objects?
	# [yes, we can use id(x) and do a linear search]

	# Dynamic producers:
	# HTTP/1.0: we must close the channel, because it's dynamic output
	# HTTP/1.1: we can use the chunked transfer-encoding, and leave
	#   it open.

	def handle_request (self, request):
		[path, params, query, fragment] = split_path (request.uri)
		self.hit_counter.increment()
		if path == '/status':
			up_time = string.join (english_time (long(time.time()) - START_TIME))
			request['Content-Type'] = 'text/html'
			request.push (
				'<html>'
				'<title>Medusa Status Reports</title>'
				'<body bgcolor="#ffffff">'
				'<h1>Medusa Status Reports</h1>'
				'<b>Up:</b> %s' % up_time
				)
			for i in range(len(self.objects)):
				request.push (self.objects[i].status())
				request.push ('<hr>\r\n')
			request.push (
				'<p><a href="/status/channel_list">Channel List</a>'
				'<hr>'
				'<img src="/status/medusa.gif" align=right width=%d height=%d>' % (
					medusa_gif.width,
					medusa_gif.height
					) +
				'</body></html>'
				)
			request.done()

		elif path == '/status/channel_list':
			request['Content-Type'] = 'text/html'
			request.push ('<html><body>')
			request.push(channel_list_producer())
			request.push (
				'<hr>'
				'<img src="/status/medusa.gif" align=right width=%d height=%d>' % (
					medusa_gif.width,
					medusa_gif.height
					) +
				'</body></html>'
				)
			request.done()

		elif path == '/status/medusa.gif':
			request['Content-Type'] = 'image/gif'
			request['Content-Length'] = len(medusa_gif.data)
			request.push (medusa_gif.data)
			request.done()

		elif path == '/status/close_zombies':
			message = (
				'<h2>Closing all zombie http client connections...</h2>'
				'<p><a href="/status">Back to the status page</a>'
				)
			request['Content-Type'] = 'text/html'
			request['Content-Length'] = len (message)
			request.push (message)
			now = int (time.time())
			for channel in asyncore.socket_map.keys():
				if channel.__class__ == http_server.http_channel:
					if channel != request.channel:
						if (now - channel.creation_time) > channel.zombie_timeout:
							channel.close()
			request.done()

		# Emergency Debug Mode
		# If a server is running away from you, don't KILL it!
		# Move all the AF_INET server ports and perform an autopsy...
		# [disabled by default to protect the innocent]
		#elif path == '/status/emergency_debug':
		elif 0:
			request.push ('<html>Moving All Servers...</html>')
			request.done()
			for channel in asyncore.socket_map.keys():
				if channel.accepting:
					if type(channel.addr) is type(()):
						ip, port = channel.addr
						channel.socket.close()
						channel.del_channel()
						channel.addr = (ip, port+10000)
						fam, typ = channel.family_and_type
						channel.create_socket (fam, typ)
						channel.set_reuse_addr()
						channel.bind (channel.addr)
						channel.listen(5)

		elif self.hyper_regex.match (path) != -1:
			oid = string.atoi (self.hyper_regex.group (1))
			for object in self.hyper_objects:
				if id (object) == oid:
					if hasattr (object, 'hyper_respond'):
						object.hyper_respond (self, path, request)
		else:
			request.error (404)
			return

	def status (self):
		return producers.simple_producer (
			'<li>Status Extension <b>Hits</b> : %s' % self.hit_counter
			)

	def register_hyper_object (self, object):
		if not object in self.hyper_objects:
			self.hyper_objects.append (object)

import logger

class logger_for_status (logger.tail_logger):

	def status (self):
		return 'Last %d log entries for: %s' % (
			len (self.messages),
			html_repr (self)
			)

	def hyper_respond (self, sh, path, request):
		request['Content-Type'] = 'text/plain'
		messages = self.messages[:]
		messages.reverse()
		request.push (lines_producer (messages))
		request.done()

class lines_producer:
	def __init__ (self, lines):
		self.lines = lines

	def ready (self):
		return len(self.lines)

	def more (self):
		if self.lines:
			chunk = self.lines[:50]
			self.lines = self.lines[50:]
			return string.join (chunk, '\r\n') + '\r\n'
		else:
			return ''

class channel_list_producer (lines_producer):
	def __init__ (self):
		channel_reprs = map (
			lambda x: '&lt;' + repr(x)[1:-1] + '&gt;',
			asyncore.socket_map.keys()
			)
		channel_reprs.sort()
		lines_producer.__init__ (
			self,
			['<h1>Active Channel List</h1>',
			 '<pre>'
			 ] + channel_reprs + [
				 '</pre>',
				 '<p><a href="/status">Status Report</a>'
				 ]
			)


# this really needs a full-blown quoter...
def sanitize (s):
	if '<' in s:
		s = string.join (string.split (s, '<'), '&lt;')
	if '>' in s:
		s = string.join (string.split (s, '>'), '&gt;')
	return s

def html_repr (object):
	so = sanitize (repr (object))
	if hasattr (object, 'hyper_respond'):
		return '<a href="/status/object/%d/">%s</a>' % (id (object), so)
	else:
		return so

def html_reprs (list, front='', back=''):
	reprs = map (
		lambda x,f=front,b=back: '%s%s%s' % (f,x,b),
		map (lambda x: sanitize (html_repr(x)), list)
		)
	reprs.sort()
	return reprs

# for example, tera, giga, mega, kilo
# p_d (n, (1024, 1024, 1024, 1024))
# smallest divider goes first - for example
# minutes, hours, days
# p_d (n, (60, 60, 24))

def progressive_divide (n, parts):
	result = []
	for part in parts:
		n, rem = divmod (n, part)
		result.append (rem)
	result.append (n)
	return result

# b,k,m,g,t
def split_by_units (n, units, dividers, format_string):
	divs = progressive_divide (n, dividers)
	result = []
	for i in range(len(units)):
		if divs[i]:
			result.append (format_string % (divs[i], units[i]))
	result.reverse()
	if not result:
		return [format_string % (0, units[0])]
	else:
		return result

def english_bytes (n):
	return split_by_units (
		n,
		('','K','M','G','T'),
		(1024, 1024, 1024, 1024, 1024),
		'%d %sB'
		)

def english_time (n):
	return split_by_units (
		n,
		('secs', 'mins', 'hours', 'days', 'weeks', 'years'),
		(         60,     60,      24,     7,       52),
		'%d %s'
		)
