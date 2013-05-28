#SublimeServer

####Allow you run a HTTP Server in SublimeText 2, and serves all the open project folders

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

###For more details please visit http://learning.github.com/SublimeServer
