# Editor-Scripts-Symbols
Anki addon to run custom scripts and insert symbols/strings in the Anki editor using keyboard shortcuts or popup menus.

Configure symbols/strings, JavaScript or Python snippets to be inserted/executed in the editor from keyboard shortcuts (Qt format, see https://doc.qt.io/qt-5/qkeysequence.html).

<img src="https://aws1.discourse-cdn.com/standard11/uploads/anki2/original/2X/e/e0a25dd14a1fc50f0f868ff38698913a42a71b99.png" height="200">
<img src="https://aws1.discourse-cdn.com/standard11/uploads/anki2/original/2X/b/b1cd176578f2ea2549c111e525e7a39719c58c18.png" height="250">
<img src="https://aws1.discourse-cdn.com/standard11/uploads/anki2/original/2X/1/18a683d2c9fa656bce473a884611b2550e93bed4.png" height="300">

**CONFIGURATION**
Sample configuration included with addon. Add menu entries in add-on configuration by adding JSON objects and lists in hierarchal "node tree" where each node is one of the following:
- Menu: Node is menu containing end nodes and/or submenus. Keys:
- Mandatory:
- Menu: Menu name.
- Items: JSON list of children.
  - Optional:
    - Shortcut: Keyboard shortcut to open menu at caret position.
- Symbol: Node is symbol/string to insert. Keys:
  - Mandatory:
    - Symbol: Symbol/string to insert
  - Optional:
    - HTML: Set to string "true" to interpret string as HTML: "HTML": "true" (defaults to false).
    - Shortcut: Keyboard shortcut to insert symbol/string.
    - Script/JavaScript: Node is JavaScript to execute in editor. The script is executed through document.execCommand(), the note contents are in the shadow root (document.activeElement.shadowRoot). The clipboard contents are made available in the object "ess_clipboard": ess_clipboard = {html: [clipboard HTML content], text: [clipboard text content]}. Keys:
  - Mandatory:
    - Script: Title/name of script.
    - Language: Script language, must be "JS" "Language": "JS".
    - At least one of "Pre", "File", "Post" (see below), otherwise nothing will be executed.
  - Optional:
    - Pre: JavaScript command(s) to prepend to the file contents.
    - File: File to load script commands from in [addon]/user_files.
    - Post: JavaScript command(s) to append to the file contents.
    - Shortcut: Keyboard shortcut to execute script.
- Script/Python: Node is Python to execute in editor. The script is executed through compile/exec statements. The Anki Editor object instance is available through the variable "editor", the QApplication clipboard is available through the variable "clipboard" and the main window object through the variable "mw". Keys:
  - Mandatory:
    - Script: Title/name of script.
    - Language: Script language, must be "PY" "Language": "PY".
    - At least one of "Pre", "File", "Post" (see below), otherwise nothing will be executed.
  - Optional:
    - Pre: Python command(s) to prepend to the file contents.
    - File: File to load script commands from in [addon]/user_files.
    - Post: JavaScript command(s) to append to the file contents.
    - Shortcut: Keyboard shortcut to execute script.
<pre><code>
{
	"Menu": "Context menu - this node corresponds to the context menu",
	"Shortcut": "Ctrl+Shift+F1",
	"Items":
	[
		{
			"Menu": "A submenu",
			"Shortcut": "Ctrl+Shift+F2",
			"Items":
			[
				{
					"Menu": "A sub-submenu",
					"Shortcut": "Ctrl+Shift+F3",
					"Items":
					[
						{
							"HTML": "false",
							"Shortcut": "Ctrl+Shift+F4",
							"Symbol": "Will insert this text in plain text"
						},
						{
							"HTML": "true",
							"Shortcut": "Ctrl+Shift+F5",
							"Symbol": "Will insert this text in HTML format"
						}		
					]
				},
				{
					"Script": "Sample JS",
					"Language": "JS",
					"Pre": "console.log(`The clipboard contents: ${ess_clipboard['text']}`);",
					"File": "",
					"Post": "",
					"Shortcut": "Ctrl+Shift+F6"
				}
			]
		},
		{
			"Script": "Sample python",
			"Language": "PY",
			"Pre": "print(f'The Editor object instance: {editor}')",
			"File": "",
			"Post": "",
			"Shortcut": "Ctrl+Shift+F7"
		}
	]
}
</code></pre>

**MISC**
In addition to being available from keyboard shortcuts the entire "tree" is available in the editor context menu (right click).
Feel free to share your script snippets in https://forums.ankiweb.net/t/useful-javascript-snippets-for-the-editor/14536

**CHANGELOG**
Reimplementation from "Editor JS snippets": new format of config file (see above) to allow arbitrary submenu structure (unfortunately breaks previous configs), added python script support, added clipboard content to JavaScript environment, change addon name to match use.
