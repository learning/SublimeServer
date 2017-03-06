# ------------------------------------------------------------------------------
# SublimeServer 0.3.3
# ------------------------------------------------------------------------------
__VERSION__ = "0.3.3"

import os
import sys
import sublime
import sublime_plugin
import threading
import webbrowser
import posixpath
import socket
import cgi
import shutil
import mimetypes
import time
import io

# detect python's version
python_version = sys.version_info[0]

# Sublime 3 (Python 3.x)
if python_version == 3:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn, TCPServer
    # from io import StringIO
    from urllib import parse as urllib

# Sublime 2 (Python 2.x)
else:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn, TCPServer
    # from StringIO import StringIO
    import urllib

# SublimeServer Settings
settings = None
# HTTP server thread
thread = None
# Open directories
dic = None
# Fail attempts
attempts = 0
# Sublime complete loaded?
loaded = False


def load_settings():
    '''Load SublimeServer Settings'''
    # default settings
    defaultPort = 8080
    # default attempts
    defaultAttempts = 5
    # default interval
    defaultInterval = 500
    # default mimeType
    defaultMimeTypes = {
        '': 'application/octet-stream',  # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
    }
    # default autorun
    defaultAutorun = False
    # default extension
    defaultExtension = '.html'

    # load SublimeServer settings
    s = sublime.load_settings('SublimeServer.sublime-settings')

    # if setting file not exists, set to default
    if not s.has('port'):
        s.set('port', defaultPort)
    if not s.has('attempts'):
        s.set('attempts', defaultAttempts)
    if not s.has('interval'):
        s.set('interval', defaultInterval)
    if not s.has('mimetypes'):
        s.set('mimetypes', defaultMimeTypes)
    if not s.has('autorun'):
        s.set('autorun', defaultAutorun)
    if not s.has('defaultExtension'):
        s.set('defaultExtension', defaultExtension)

    # Normalize base path.
    if s.has('base'):
        base = s.get('base')
        base = base.replace('\\', '/')
        if not base.endswith('/'):
            base += '/'
        s.set('base', base)

    sublime.save_settings('SublimeServer.sublime-settings')

    # Merge project and user settings.
    window = sublime.active_window()
    if window:
        view = window.active_view()
        if view:
            settings = view.settings()
            if settings:
                serverSettings = settings.get('SublimeServer')
                if serverSettings:
                    for setting in serverSettings:
                        s.set(setting, serverSettings.get(setting))

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
            if key in dic.keys():
                if dic[key] is f:
                    continue
                else:
                    loop = True
                    num = 0
                    while(loop):
                        num += 1
                        k = key + " " + str(num)
                        if k in dic.keys():
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


class SublimeServerHandler(BaseHTTPRequestHandler):

    extensions_map = {}
    defaultExtension = None
    base_path = None

    def version_string(self):
        '''overwrite HTTP server's version string'''
        return 'SublimeServer/%s Sublime/%s' % (__VERSION__, sublime.version())


    def do_GET(self):
        """Serve a GET request."""

        # special case for .md files
        path = self.translate_path(self.path)
        if not os.path.isdir(path):
            ctype = self.guess_type(path)
            # ".md": "text/x-markdown; charset=UTF-8",
            if ctype and ctype.startswith("text/x-markdown"):
                self.send_md()
                return 

        f = self.send_head()
        if f:
            try:
                self.copyfile(f, self.wfile)
            finally:
                f.close()

    def do_OPTIONS(self):
        """Serve a OPTIONS request."""
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        """Serve a POST request."""
        self.do_GET()

    def do_PUT(self):
        """Serve a PUT request."""
        self.do_GET()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if path is None:
            self.send_error(404, "File not found")
            return None
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

        # If there's no extension and the file doesn't exist,
        # see if the file plus the default extension exists.
        if (SublimeServerHandler.defaultExtension and
            not posixpath.splitext(path)[1] and
            not posixpath.exists(path) and
            posixpath.exists(path + SublimeServerHandler.defaultExtension)):
            path += SublimeServerHandler.defaultExtension

        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        try:
            self.send_response(200)
            self.send_header("Content-type", ctype)
            fs = os.fstat(f.fileno())
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header(
                "Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except:
            f.close()
            raise

    def send_md(self):
        path = self.translate_path(self.path)
        try:
            TEMPLATE = """
                <!DOCTYPE html>
                <html>
                  <body>
                    <div id="preview"></div>
                    <div id="markdown" style="visibility:hidden;">%s</div>
                    <script src="/markdown.js"></script>
                    <script>
                    window.addEventListener('load', function() {
                        var markdown_src = document.getElementById("markdown").textContent;
                        var preview = document.getElementById("preview");
                        preview.innerHTML = markdown.toHTML(markdown_src);
                    });
                    </script>
                  </body>
                </html>
                """
            html = TEMPLATE % open(path,"r",encoding='utf8').read()
        except IOError:
            self.send_error(404, "File not found")
            return None
        encoded = html.encode(sys.getfilesystemencoding())
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(encoded))
        self.send_header("Last-Modified", time.time())
        self.end_headers()
        
        self.copyfile(f, self.wfile)
        f.close()
        # self.wfile.write(html)

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
                self.send_error(403, "Access Denied")
                return None
            list.sort(key=lambda a: a.lower())
        # f = StringIO()
        r = []
        displaypath = cgi.escape(urllib.unquote(self.path))
        enc = sys.getfilesystemencoding()
        r.append('<!DOCTYPE html>')
        r.append('<html>\n<head>\n<meta charset="%s"/>\n' % enc)
        r.append('<title>SublimeServer %s</title>\n</head>\n' % displaypath)
        r.append('<link rel="stylesheet" type="text/css" href="/SublimeServer.css">')
        r.append('<body>\n<h2>SublimeServer %s</h2>\n' % displaypath)
        r.append('<hr>\n<ul>\n')
        # output open directories
        if root is True:
            for key in dic:
                r.append('<li><a href="%s">%s/</a>\n' % (
                    urllib.quote(key), cgi.escape(key)))
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
                r.append('<li><a href="%s">%s</a>\n' % (
                    urllib.quote(linkname), cgi.escape(displayname)))
        r.append("</ul>\n<hr>\n</body>\n</html>\n")
        encoded = ''.join(r).encode(enc)
        f = io.BytesIO()
        f.write(encoded)
        # length = f.tell()
        f.seek(0)
        self.send_response(200)
        # encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(encoded))
        self.end_headers()
        return f

    def translate_path(self, path):
        global dic
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        path = posixpath.normpath(urllib.unquote(path))
        if path == '/':
            sublime.set_timeout(
                lambda: sublime.run_command('sublimeserver_reload'), 0)
            # sleep 0.001 second to wait SublimeserverReloadCommand done
            # any else sulotion?
            time.sleep(0.001)
            return path
        # the browser try to get favourite icon
        if path == '/favicon.ico':
            return sublime.packages_path() + "/SublimeServer/favicon.ico"

        elif path == '/SublimeServer.css':
            return sublime.packages_path() + "/SublimeServer/style.example.css"

        # markdown java script from https://github.com/evilstreak/markdown-js
        elif path == '/markdown.js':
            return sublime.packages_path() + "/SublimeServer/markdown.js"

        if SublimeServerHandler.base_path:
            path = SublimeServerHandler.base_path + path

        # else, deal with path...
        words = path.split('/')
        words = filter(None, words)
        if python_version == 3:
            tmp = []
            try:
                while True:
                    tmp.append(next(words))
            except StopIteration:
                words = tmp

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
        if ext in SublimeServerHandler.extensions_map:
            return SublimeServerHandler.extensions_map[ext]
        ext = ext.lower()
        if ext in SublimeServerHandler.extensions_map:
            return SublimeServerHandler.extensions_map[ext]
        else:
            return SublimeServerHandler.extensions_map['']


class SublimeServerThreadMixIn(ThreadingMixIn, TCPServer):
    pass


class SublimeServerThread(threading.Thread):
    httpd = None

    def __init__(self):
        settings = load_settings()
        super(SublimeServerThread, self).__init__()
        if not mimetypes.inited:
            mimetypes.init()  # try to read system mime.types
        SublimeServerHandler.extensions_map = mimetypes.types_map.copy()
        SublimeServerHandler.extensions_map.update(settings.get('mimetypes'))
        SublimeServerHandler.base_path = settings.get('base')
        SublimeServerHandler.defaultExtension = settings.get('defaultExtension')
        self.httpd = SublimeServerThreadMixIn(('', settings.get('port')), SublimeServerHandler)

        self.setName(self.__class__.__name__)

    def run(self):
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class SublimeserverStartCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        global settings, thread, dic, attempts
        settings = load_settings()
        if thread is not None and thread.is_alive():
            return sublime.message_dialog('SublimeServer Alread Started!')
        try:
            dic = get_directories()
            thread = SublimeServerThread()
            thread.start()
            sublime.status_message('SublimeServer Started!')
            attempts = 0
        except socket.error as error:
            attempts += 1
            if attempts > settings.get('attempts'):
                # max attempts reached
                # reset attempts to 0
                attempts = 0
                sublime.message_dialog('Unknow Error')
                # try:
                #     sublime.message_dialog(message)
                # except UnicodeDecodeError:
                #     sublime.message_dialog(message.decode(sys.getfilesystemencoding()))
            else:
                # try another attempt
                sublime.set_timeout(
                    lambda: sublime.run_command('sublimeserver_start'),
                    settings.get('interval'))

    def is_enabled(self):
        global thread
        return not (thread is not None and thread.is_alive())


class SublimeserverStopCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        global thread
        if thread is not None and thread.is_alive():
            thread.stop()
            thread.join()
            thread = None
        sublime.status_message('SublimeServer Stopped!')

    def is_enabled(self):
        global thread
        return thread is not None and thread.is_alive()


class SublimeserverRestartCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        global settings
        sublime.run_command('sublimeserver_stop')
        sublime.set_timeout(
            lambda: sublime.run_command('sublimeserver_reload'), 0)
        sublime.set_timeout(
            lambda: sublime.run_command('sublimeserver_start'),
            settings.get('interval'))

    def is_enabled(self):
        global thread
        return thread is not None and thread.is_alive()


class SublimeserverReloadCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        global dic, get_directories, settings, load_settings
        dic = get_directories()
        settings = load_settings()


class SublimeserverBrowserCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global dic, settings, thread, get_directories
        settings = load_settings()
        if thread is None or not thread.is_alive():
            return sublime.message_dialog('SublimeServer isn\'t Started yet!')
        # if dic is None:
        dic = get_directories()
        url = "http://localhost:{0}/{1}"
        filename = self.view.file_name()
        base = settings.get('base')
        # Find the file.
        for k in dic:
            if filename.startswith(dic[k]):
                path = k + filename[len(dic[k]):]
                # Normalize path for Windows users.
                path = path.replace('\\', '/')
                # Remove base path from URL. It's assumed by server.
                if base and path.startswith(base):
                    path = path[len(base):]
                url = url.format(settings.get('port'), path)
                return webbrowser.open(url)
        rawname = filename.split(os.path.sep)[-1]
        sublime.message_dialog(
            'File %s not in Sublime Project Folder!' % rawname)

    def is_enabled(self):
        global thread
        return thread is not None and thread.is_alive()


class SublimeserverAutorun(sublime_plugin.EventListener):
    def on_activated(self, view):
        global loaded, settings
        if loaded:
            return
        loaded = True
        # if autorun set to True
        if settings.get('autorun') and thread is None:
            sublime.run_command('sublimeserver_start')

# load settings now
settings = load_settings()
# For ST3
def plugin_loaded():
    global settings
    settings = load_settings()

# check if last SublimeServerThread exists
threads = threading.enumerate()
for t in threads:
    if t.__class__.__name__ is SublimeServerThread.__name__:
        thread = t
        break
