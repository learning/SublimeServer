import sublime, sublime_plugin  
  
class SublimeserverCommand(sublime_plugin.WindowCommand):  
    # list of open directories
    dirList =[]
    # list of operations
    opList = ["Start SublimeServer", "Stop SublimeServer", "Restart SublimeServer"]
    # SublimeServer settings
    s = None

    defaultSettings = {"name": "SublimeServer","version": "0.0.1"}

    def __init__(self, *args, **kwargs):
        super(SublimeserverCommand, self).__init__(*args, **kwargs)
        # load SublimeServer settings
        # s = sublime.load_settings('SublimeServer.sublime-settings')
        # if not s.has('config'):
        #     s.set('config', self.defaultSettings)
        # sublime.save_settings('SublimeServer.sublime-settings')

    def run(self):
        windows = sublime.windows()
        for w in windows:
            fs = w.folders()
        for f in fs:
            if f in self.dirList:
                continue
            else:
                self.dirList.append(f)
        self.window.show_quick_panel(self.dirList, self.callback)


    def callback(self, index):
        sublime.message_dialog(self.dirList[index])
