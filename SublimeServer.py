import sublime, sublime_plugin
import webbrowser

def load_settings():
    '''Load SublimeServer Settings'''

    # default settings
    defaultPort = 8080

    # load SublimeServer settings
    s = sublime.load_settings('SublimeServer.sublime-settings')
    # if setting file not exists, set to default
    if not s.has('port'):
        s.set('port', self.defaultPort)
    # sublime.save_settings('SublimeServer.sublime-settings')
    return s

settings = load_settings()

class SublimeserverCommand(sublime_plugin.WindowCommand):  
    # list of open directories
    dirList =[]
    # list of operations
    opList = ["Start SublimeServer", "Stop SublimeServer", "Restart SublimeServer"]

    def run(self):
        # retrieve all Sublime windows
        windows = sublime.windows()
        for w in windows:
            # and retrieve all unique directory path
            fs = w.folders()
            for f in fs:
                if f in self.dirList:
                    continue
                else:
                    self.dirList.append(f)
        self.window.show_quick_panel(self.dirList, self.callback)


    def callback(self, index):
        sublime.message_dialog(self.dirList[index])

class SublimeserverStartCommand(sublime_plugin.WindowCommand):
    def run(self):
        sublime.message_dialog('Start SublimeServer')

class SublimeserverStopCommand(sublime_plugin.WindowCommand):
    def run(self):
        sublime.message_dialog('Stop SublimeServer')

class SublimeserverRestartCommand(sublime_plugin.WindowCommand):
    def run(self):
        sublime.message_dialog('Restart SublimeServer')

class SublimeserverBrowserCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        webbrowser.open("http://127.0.0.1:{0}{1}".format(settings.get('port'), self.view.file_name()))
