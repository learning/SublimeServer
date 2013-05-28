#SublimeServer

####Allow you run a HTTP Server in SublimeText 2, and serves all the open project folders

------

## Markdown Rendering
When requested a Markdown file(.md) the server returns an Html file that will reder Markdown syntax in the Html file into Html Syntax later.

### Setup
Add mime types
Open Tools-SublimeServer-Settings, add Markdown mime types like below
`{
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
}`

 
###For more details please visit http://learning.github.com/SublimeServer
