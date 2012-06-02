__version__ = "0.1.0"

# SublimeServer Settings
settings = None
# HTTP server thread
thread = None
# Open directories
dic = None
# Fail attempts
attempts = 0

import sublime, sublime_plugin
import webbrowser
import os
import posixpath
import BaseHTTPServer
from SocketServer import TCPServer
import socket
import threading
import urllib
import cgi
import sys
import shutil
import mimetypes
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def load_settings():
    '''Load SublimeServer Settings'''
    # default settings
    defaultPort = 8080
    # default attempts
    defaultAttempts = 5
    # default interval
    defaultInterval = 500

    # load SublimeServer settings
    s = sublime.load_settings('SublimeServer.sublime-settings')
    # if setting file not exists, set to default
    if not s.has('port'):
        s.set('port', defaultPort)
    if not s.has('attempts'):
        s.set('attempts', defaultAttempts)
    if not s.has('interval'):
        s.set('interval', defaultInterval)
    return s

def get_directories():
    '''Get Open Directories in Sublime'''
    dic = {}
    # retrieve all Sublime windows
    windows = sublime.windows()
    for w in windows:
        # and retrieve all unique directory path
        fs = w.folders()
        for f in fs:
            key = f.split(os.path.sep)[-1]
            if dic.has_key(key):
                if dic[key] is f:
                    continue
                else:
                    loop = True
                    num = 0
                    while(loop):
                        num += 1
                        k = key + " " + str(num)
                        if dic.has_key(k):
                            if dic[k] is f:
                                loop = False
                                break
                        else:
                            dic[k] = f
                            loop = False
                            break
            else:
                dic[key] = f
    return dic

settings = load_settings()

class SublimeServer(BaseHTTPServer.BaseHTTPRequestHandler):

    """The SublimeServer HTTP Request Handler, 
    Modified from Python's SimpleHTTPServer 0.6
    """

    server_version = "SublimeServer/" + __version__

    # dic = get_directories()

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if path is '/':
            return self.list_directory(path)
        if os.path.isdir(path):

            # not endswidth /
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None

            # looking for index.html or index.htm
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)

        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    # Maybe we can using template
    def list_directory(self, path):
        global dic
        # a flag to mark if current directory is root
        root = False
        # request the root directory
        # and show the open directories in sublime
        if path is '/':
            root = True
        else:
            try:
                list = os.listdir(path)
            except os.error:
                self.send_error(404, "No permission to list directory")
                return None
            list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html>')
        f.write("<html>\n<head>\n<meta charset=\"utf-8\"/>\n")
        f.write("<title>SublimeServer %s</title>\n</head>\n" % displaypath)
        f.write("<body>\n<h2>SublimeServer %s</h2>\n" % displaypath)
        f.write("<hr>\n<ul>\n")
        # output open directories
        if root is True:
            for key in dic:
                f.write('<li><a href="%s">%s/</a>\n'
                        % (urllib.quote(key), cgi.escape(key)))
        else:
            for name in list:
                fullname = os.path.join(path, name)
                displayname = linkname = name
                # Append / for directories or @ for symbolic links
                if os.path.isdir(fullname):
                    displayname = name + "/"
                    linkname = name + "/"
                if os.path.islink(fullname):
                    displayname = name + "@"
                    # Note: a link to a directory displays with @ and links with /
                f.write('<li><a href="%s">%s</a>\n'
                        % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        global dic
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        if path == '/':
            return path
        # the browser try to get favourite icon
        if path == '/favicon.ico':
            return sublime.packages_path() + "/SublimeServer/favicon.ico"
        # else, deal with path...
        words = path.split('/')
        words = filter(None, words)
        if words[0] in dic:
            path = dic[words[0]]
            for word in words[1:]:
                path = os.path.join(path, word)
            return path
        else:
            return None

    def copyfile(self, source, outputfile):
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })

class SublimeServerThread(threading.Thread):
    httpd = None

    def __init__(self):
        global settings
        self.httpd = TCPServer(("", settings.get('port')), SublimeServer)
        threading.Thread.__init__(self)
        
    def run(self):        
        self.httpd.serve_forever()
        self._stop = threading.Event()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self._stop.set()

class SublimeserverStartCommand(sublime_plugin.WindowCommand):
    def run(self):
        global setting, thread, dic, attempts
        if type(thread) is SublimeServerThread and threa.is_alive():
            return sublime.message_dialog('SublimeServer Alread Started!')
        if type(thread) is SublimeServerThread:
            # thread is dead
            thread = None
        try:
            dic = get_directories()
            thread = SublimeServerThread()
            thread.start()
            sublime.status_message('SublimeServer Started!')
            attempts = 0
        except socket.error, (value, message):
            attempts += 1
            if attempts > settings.get('attempts'):
                # max attempts reached
                # reset attempts to 0
                attempts = 0
                sublime.message_dialog(message)
            else:
                # try another attempt
                sublime.set_timeout(lambda: 
                    self.window.run_command('sublimeserver_start'), 
                    settings.get('interval')
                )

class SublimeserverStopCommand(sublime_plugin.WindowCommand):
    def run(self):
        global thread
        if type(thread) is SublimeServerThread:
            # Don't know how to kill a thread, just set to None
            # Any good suggedstion?
            thread.stop()
            thread = None
        sublime.status_message('SublimeServer Stopped!')

class SublimeserverRestartCommand(sublime_plugin.WindowCommand):
    def run(self):
        global settings, thread, attempts
        if type(thread) is SublimeServerThread and thread.is_alive():
            thread.stop()
            thread = None
        try:
            thread = SublimeServerThread()
            thread.start()
            sublime.status_message('SublimeServer Restart Finish!')
        except socket.error, (value, message):
            attempts += 1
            if attempts > settings.get('attempts'):
                # max attempts reached
                attempts = 0
                sublime.message_dialog(message)
            else:
                sublime.set_timeout(lambda: 
                    self.window.run_command('sublimeserver_restart'), 
                    settings.get('interval')
                )

class SublimeserverBrowserCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global dic, settings, thread
        if thread is None or not thread.is_alive():
            return sublime.message_dialog('SublimeServer isn\'t Started yet!')
        if dic is None:
            dic = get_directories()
        url = "http://localhost:{0}/{1}"
        filename = self.view.file_name()
        for k in dic:
            if filename.startswith(dic[k]):
                url = url.format(settings.get('port'), 
                    k + filename[dic[k].__len__():])
                return webbrowser.open(url)
        rawname = filename.split(os.path.sep)[-1]
        sublime.message_dialog('File %s not in Sublime Project Folder!' % rawname)