import sys, os, codecs
from typing import Dict
from anki.hooks import addHook
from aqt import mw, gui_hooks
from aqt.utils import *
from aqt.qt import QMenu, QKeySequence, QApplication, QClipboard

MENU = "Menu"
SYMBOL = "Symbol"
HTML = "HTML"
ITEMS = "Items"
SHORTCUT = "Shortcut"
SCRIPT = "Script"
LANG = "Language"
JS = "js"
PY = "py"
PRE = "Pre"
FILE = "File"
POST = "Post"
CMD = "cmd"
LBL = "lbl"
ADDON_TITLE = "Editor Scripts & Symbols"
ess_cmds = {}


# Build the JS commands from pre/post and file contents
def build_js(pre, fname, post) -> str:
    file = ""
    if fname:
        path = os.path.join(os.path.dirname(__file__), f"user_files/{fname}")
        with codecs.open(path, encoding='utf-8') as fh:
            file = fh.read().strip()
    return pre + file + post


# Build the PY commands from pre/post and file contents
def build_py(pre, fname, post):
    file = ""
    if fname:
        path = os.path.join(os.path.dirname(__file__), f"user_files/{fname}")
        with codecs.open(path, encoding='utf-8') as fh:
            file = fh.read()
    return compile(f"{pre}\n{file}\n{post}\n", fname if fname else "<string>", "exec")


# Build and show menu from node and down at current caret position
def show_submenu(node, editor):
    def pop_submenu(pos):
        menu = build_menu(node, None, editor)
        menu.popup(editor.web.mapToGlobal(QPoint(pos[0], pos[1])))
    editor.web.evalWithCallback("document.activeElement.focus(); sel = document.activeElement.shadowRoot.getSelection(); rng = sel.getRangeAt(sel.rangeCount - 1).cloneRange(); tmp_rng = document.createRange(); tmp_rng.setStart(sel.anchorNode, sel.anchorOffset); tmp_rng.setEnd(sel.focusNode, sel.focusOffset); rng.collapse(tmp_rng.collapsed); rect = rng.getBoundingClientRect(); [rect.x + rect.width, rect.y + rect.height]", pop_submenu)


# Run py cmd in correct context
def exec_py(cmd, editor):
    exec(cmd, {"editor": editor, "clipboard": QApplication.clipboard(), "mw": mw})


# Get clipboard contents and return "JS hash table" in string with contents
def clipboard() -> str:
    mime = QApplication.clipboard().mimeData(QClipboard.Mode.Clipboard)
    return r'{html: `' + mime.html() + '`, text: `' + mime.text() + '`}'


# Recursively take config node dict - parse and build commands
def build_cmds(node) -> Dict:
    if type(node) is dict:
        out = {}
        if ITEMS in node:
            out[LBL] = node[MENU] if MENU in node else ""
            out[CMD] = lambda editor: lambda: show_submenu(out, editor)
            out[ITEMS] = []
            for subnode in node[ITEMS]:
                tmp_node = build_cmds(subnode)
                if tmp_node:
                    out[ITEMS].append(tmp_node)
        elif LANG in node and node[LANG].lower() == JS:
            out[LBL] = node[SCRIPT]
            out[CMD] = lambda editor, cmd=build_js(node.get(PRE) or "", node.get(FILE) or "", node.get(POST) or ""): lambda: editor.web.eval(f"ess_clipboard = {clipboard()};\n{cmd}")
        elif LANG in node and node[LANG].lower() == PY:
            out[LBL] = node[SCRIPT]
            out[CMD] = lambda editor, cmd=build_py(node.get(PRE) or "", node.get(FILE) or "", node.get(POST) or ""): lambda: exec_py(cmd, editor)
        elif SYMBOL in node:
            out[LBL] = node[SYMBOL]
            out[CMD] = lambda editor, cmd=f"document.execCommand(`{'insertHTML' if node[HTML] == 'true' else 'insertText'}`, false, `{node[SYMBOL]}`);": lambda: editor.web.eval(cmd)
        else:
            err = "<p>Unknown configuration entry:</p><ul>"
            for key, val in node.items():
                err += f"<li>{key}: {val}</li>"
            err += "</ul><p>Ignoring entry.</p>"
            showWarning(text=err, parent=mw, title=ADDON_TITLE, textFormat="rich")
            return None
        out[SHORTCUT] = QKeySequence(node[SHORTCUT]) if SHORTCUT in node and node[SHORTCUT] else 0
        return out
    else:
        showWarning(text=f"<p>Incorrect configuation entry, expected dict type entry, found {type(node)}, ignoring.</p>", parent=mw, title=ADDON_TITLE, textFormat="rich")
        return None


# Recursively take config dict - parse and add shortcuts
def build_shortcuts(node, scuts, editor):
    if SHORTCUT in node:
        scuts.append([node[SHORTCUT], node[CMD](editor)])
    if ITEMS in node:
        for subnode in node[ITEMS]:
            build_shortcuts(subnode, scuts, editor)


# Recursively take config dict - parse - return QMenu
def build_menu(node, menu, editor) -> QMenu:
    if not menu:
        menu = QMenu(editor.web)
    if ITEMS in node:
        for subnode in node[ITEMS]:
            if ITEMS in subnode:
                menu_action = menu.addMenu(build_menu(subnode, None, editor))
                menu_action.setText(subnode[LBL])
            else:
                menu.addAction(subnode[LBL], subnode[CMD](editor), subnode[SHORTCUT])
    else:
        menu.addAction(node[LBL], node[CMD](editor), node[SHORTCUT])
    return menu


# Take config and recursively parse and add shortcuts
def register_shortcuts(scuts, editor):
    build_shortcuts(ess_cmds, scuts, editor)


# Context menu activation - build and append ESS menu items
def mouse_context(wedit, menu):
    if ITEMS in ess_cmds:
        menu.addSeparator()
        menu = build_menu(ess_cmds, menu, wedit.editor)
        menu.addSeparator()


# Only set up if not already loaded
if not 2065559429 in sys.modules:
    ess_cmds = build_cmds(mw.addonManager.getConfig(__name__))
    gui_hooks.editor_did_init_shortcuts.append(register_shortcuts)
    addHook('EditorWebView.contextMenuEvent', mouse_context) # Legacy hook but it does fire
    #gui_hooks.editor_will_show_context_menu.append(mouse_context) # New style hooks doesn't fire until Image Occlusion Enhanced is fixed
