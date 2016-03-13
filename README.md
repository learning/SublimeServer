# SublimeServer

#### Turn you Sublime Text editor into a HTTP server, and serves all the open project folders, now support ST2 and ST3

------

## Markdown Rendering
When a client requests a Markdown file(.md), the server will return an Html file instead of the requested Markdown file, the Html file contains all of content of the Markdown file and will render Markdown syntax into Html syntax on the client side.

### Setup
Open Tools-SublimeServer-Settings, add mime types for Markdown like below

	{
		"attempts": 5,
		"autorun": false,
		"interval": 500,
		"mimetypes":
		{
			"": "application/octet-stream",
			".c": "text/plain",
			".h": "text/plain",
			".markdown": "text/x-markdown; charset=UTF-8",
			".md": "text/x-markdown; charset=UTF-8",
			".py": "text/plain"
		},
		"port": 8080
	}

------

### Change Log

#### 0.3.3 - Mar 6, 2016

- Fix bug [#25](https://github.com/learning/SublimeServer/issues/25) 
- Add OPTIONS, PUT, POST support, thanks [fantonangeli](https://github.com/fantonangeli)

#### 0.3.2 - Oct 12, 2014

- Add markdown support, thanks rookiecj.
- Add default stylesheet.
- Add default extension setting, thanks [jdiamond](https://github.com/jdiamond).
- Fix some ST3 problems

#### 0.3.1 - Jun 1, 2014

Add Sublime Text 3 support.

#### 0.2.1 - Aug 31, 2012

Improvements
- Add auto-start support, Thanks [sapara](https://github.com/jdiamond).(#8)

#### 0.2.0 - Jul 20, 2012

Bug fix:

While dragging new folders to Sublime or remove folders from Sublime, SublimeServer cannot refresh it.(#4)
Improvements

- Custom mime-types support.
- Disable unavailable menu items, Thanks [bizoo](https://github.com/jdiamond).(#6)

#### 0.1.2 - Jun 28, 2012

Bug fix:
- Thread still alive and cannot stop.(#2)

Misc:
- Move SublimeServer.sublime-settings to User folder.

#### 0.1.0 - Jun 02, 2012

SublimeServer can basically use

Know issues:

- While sublime reload plugins, last SublimeServer thread still alive and cannot stop it.(#2)
- While dragging new folders to Sublime or remove folders from Sublime, SublimeServer cannot refresh it.(#4)


### For more details please visit [http://learning.github.com/SublimeServer](http://learning.github.com/SublimeServer)
