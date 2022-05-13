import os
import json, base64
from anki.hooks import addHook
from aqt import mw, gui_hooks
from aqt.utils import *
from aqt.qt import QKeySequence

from . import htmlmin

if qtmajor == 6:
    from . import dialog_qt6 as dialog
elif qtmajor == 5:
    from . import dialog_qt5 as dialog

CFG_SELECTION = "Selection only"
CFG_OPEN = "Input markdown"
CFG_INSERT = "Insert markdown"
CFG_INSERT_PREVIEW = "Insert markdown (preview)"
CFG_ELEMENT_CLASS = "Element class"
CFG_SIZE_MODE = "Size mode" # "parent", "last", WIDTHxHEIGHT (e.g "1280x1024")
CFG_LAST_GEOM = "Last geometry"
CFG_EDITOR_CSS = "Editor CSS"
ADDON_TITLE = "Insert markdown"


###########################################################################
# Main dialog to edit markdown
###########################################################################
class IM_dialog(QDialog):
    ###########################################################################
    # Constructor (populates and shows dialog)
    ###########################################################################
    def __init__(self, html, parent, on_accept = None, on_reject = None):
        QDialog.__init__(self, parent)
        self.ui = dialog.Ui_dialog()
        self.ui.setupUi(self)
        self.on_accept = on_accept
        self.on_reject = on_reject

        QShortcut(QKeySequence(Qt.CTRL |  Qt.Key_Return), self).activated.connect(self.accept)
        QShortcut(QKeySequence(Qt.SHIFT | Qt.Key_Escape), self).activated.connect(self.reject)

        self.ui.btns.accepted.connect(self.accept)
        self.ui.btns.rejected.connect(self.reject)

        if html: # htmlmin does not handle NoneType string gracefully
            html = htmlmin.minify(html, remove_all_empty_space=True, keep_pre=True)
            html = re.sub(r'[ ]*<br>[ ]*', r'<br>', html, flags=re.IGNORECASE)
            html = re.sub(r'((<(b|u|i|del|sup|sub|h\d)([ ][^>]*)?>)+)<br>', r'<br>\1', html, flags=re.IGNORECASE)
            html = re.sub(r'<br>((<\/(b|u|i|del|sup|sub|h\d)([][^>]*)?>)+)', r'\1<br>', html, flags=re.IGNORECASE)

            # fix clozes that look like they should surround an entire list
            def replacer(match):
                tail = match.group(2)
                opn = len(re.findall(r'<(?:ol|ul)[^>]*>', tail))
                close = len(re.findall(r'</(?:ol|ul)[^>]*>', tail))
                print(">>>>>>>>>>>>>>>>>")
                print(f"tail: {tail}")
                print(f"opn: {opn}, close: {close}")
                if opn > 0 and opn == close:
                    if m := re.search(r'((?:</li>\s*</(?:ul|ol)>\s*)+)$', tail, flags = re.IGNORECASE):
                        i = m.start()
                        pre = tail[:i]
                        post = tail[i:] if i < len(tail) else ''
                        return match.group(1) + pre + '}}' + post 

                return match.group(0)

            html = re.sub(r'({{c\d+::)(.*?)}}', replacer, html, flags = re.IGNORECASE | re.DOTALL)
            
            #html = re.sub(r'({{c\d+::\s*<(?:ol|ul)>(?:.*?|(?:(?:<(?:ul|ol).*?>.*?</(?:ul|ol).*?>){2})*))(</li>\s*</(?:ol|ul)[^>]*?>)}}', r'\1}}\2', html, flags = re.IGNORECASE | re.DOTALL)
            #html = re.sub(r'({{c\d+::\s*<(?:ol|ul)[^>]*>.*?)(</li>\s*</(?:ol|ul)>)}}(?:<br>)?', r'\1}}\2', html, flags = re.IGNORECASE | re.DOTALL)
        else:
            html = ""

        ordinal = 0
        for cloze in re.findall(r'{{c(\d+)::', html):
            if int(cloze) > ordinal:
                ordinal = int(cloze)

        # print(f">>>>>>>\n{html}\n>>>>>>>>>>")
        self.ui.web.setHtml(f'''
        <html>
        <head>
            <script src="Showdown.next/showdown.js"></script>
            <script src="Showdown.extensions/extendedTables.js"></script>
            <script src="Showdown.extensions/superscript.js"></script>
            <script src="Showdown.extensions/asteriskHr.js"></script>
            <link rel=stylesheet href="codemirror/styles.css">
            <script src="CodeMirror/editor.bundle.js"></script>
            <style>{CFG[CFG_EDITOR_CSS]}</style>
        </head>
        <body>
            <script>
                var sd_converter = new showdown.Converter({{extensions: [
                    "extendedTables",
                    "superscript",
                    "asteriskHr"
                ]}});
                sd_converter.setFlavor('github');
                sd_converter.setOption('underline', true);
                sd_converter.setOption('strikethrough', true);
                sd_converter.setOption('simpleLineBreaks', true);
                sd_converter.setOption('tablesHeaderId', false);
                sd_converter.setOption('noHeaderId', true);
                var imd_editor = editor.create(sd_converter.makeMarkdown(`{html}`), {ordinal});
                imd_editor.focus();
            </script>
        </body>
        </html>
        ''', QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), "")))

    ###########################################################################
    # Main dialog accept
    ###########################################################################
    def accept(self) -> None:
        def cleanup(html):
            # print(f">>>>>>>>>html we got back\n{html}\n<<<<<")
            html = htmlmin.minify(html, remove_all_empty_space=True, keep_pre=True)
            html = re.sub(r'<\/p>\s*<p>', r'<br><br>', html, flags = re.IGNORECASE | re.DOTALL)
            html = re.sub(r'<\/?p>', r'', html, flags = re.IGNORECASE | re.DOTALL)
            html = re.sub(r'[ ]*<br[ \/]*>[ ]*', r'<br>', html)
            html = re.sub(r'(</(table|ol|ul)>)[ ]*', r'\1', html)
            # html = re.sub(r'(?<!\\)((?:\\\\)*)¨', r'\1<br>', html)
            #html = re.sub(r'({{c\d+::\s*<(?:ol|ul)>(?:(?:<(?:ul|ol).*?>.*?</(?:ul|ol).*?>)*)|.*?(?!</(?:ol|ul>)))(</li>\s*</(?:ol|ul)[^>]*?>)}}', r'\1\2}}', html, flags = re.IGNORECASE | re.DOTALL)
            
            # fix clozes that look like they should surround an entire list
            def replacer(match):
                opn = len(re.findall(r'<(?:ol|ul)[^>]*>', match.group(2)))
                close = len(re.findall(r'</(?:ol|ul)[^>]*>', match.group(2)))
                if opn > close:
                    tail = match.group(3)
                    inds = [i.end() for i in re.finditer(r'</(ol|ul)>', tail)]
                    i = inds[close - opn + 1]
                    pre = tail[:i]
                    post = tail[i:] if i < len(tail) else ''
                    return match.group(1) + match.group(2) + pre + '}}<br>' + post
                else:
                    return match.group(0)

            html = re.sub(r'({{c\d+::)(.*?)}}((?:\s*</li>\s*</(?:ol|ul)>)+)', replacer, html, flags = re.IGNORECASE | re.DOTALL)
            #html = re.sub(r'({{c\d+::\s*<(?:ol|ul)[^>]*>.*?)}}(</li>\s*</(?:ol|ul)>)', r'\1\2}}<br>', html, flags = re.IGNORECASE | re.DOTALL) # fix clozes that look like they should surround an entire list

            self.on_accept(html)

        if self.on_accept:
            self.ui.web.page().runJavaScript('''(function () {
                return sd_converter.makeHtml(imd_editor.state.doc.toString());
            })();''', cleanup)

        CFG[CFG_LAST_GEOM] = base64.b64encode(self.saveGeometry()).decode('utf-8')
        mw.addonManager.writeConfig(__name__, CFG)
        return super().accept()

    ###########################################################################
    # Main dialog reject
    ###########################################################################
    def reject(self):
        CFG[CFG_LAST_GEOM] = base64.b64encode(self.saveGeometry()).decode('utf-8')
        mw.addonManager.writeConfig(__name__, CFG)
        QDialog.reject(self) 


###########################################################################
# Open markdown dialog
###########################################################################
def input_md(editor, CFG):
    # Run the md editor dialog with callback for accept
    def run_dlg(html):
        dlg = IM_dialog(html, editor.parentWindow, dlg_result)

        if CFG[CFG_SIZE_MODE].lower() == 'last':
            dlg.restoreGeometry(base64.b64decode(CFG[CFG_LAST_GEOM]))
        elif match:= re.match(r'^(\d+)x(\d+)', CFG[CFG_SIZE_MODE]):
            par_geom = editor.parentWindow.geometry()
            geom = QRect(par_geom)
            scr_geom = mw.app.primaryScreen().geometry()

            geom.setWidth(int(match.group(1)))
            geom.setHeight(int(match.group(2)))    
            if geom.width() > scr_geom.width():
                geom.setWidth(scr_geom.width())
            if geom.height() > scr_geom.height():
                geom.setHeight(scr_geom.height())
            geom.moveCenter(par_geom.center())
            if geom.x() < 0:
                geom.setX(0)
            if geom.y() < 0:
                geom.setY(0)

            dlg.setGeometry(geom)
        else:
            dlg.setGeometry(editor.parentWindow.geometry())

        dlg.show()
    
    # Callback for accepted md dialog
    def dlg_result(html):
        if CFG[CFG_SELECTION]:
            editor.web.eval(f'''(function () {{
                let nd = document.activeElement.shadowRoot.querySelector('anki-editable');
                if (nd.firstChild && nd.firstChild.nodeName.toLowerCase() !== '#text') {{
                    let usr_rng = document.activeElement.shadowRoot.getSelection().getRangeAt(0);
                    document.execCommand('selectAll');
                    let all_rng = document.activeElement.shadowRoot.getSelection().getRangeAt(0);
                    if (usr_rng.toString() === all_rng.toString()) {{
                        nd.innerHTML = '<br>' + nd.innerHTML + '<br>';
                        document.execCommand('selectAll');
                    }} else {{
                        sell.removeAllRanges();
                        sell.addRange(usr_rng);
                    }}
                }} 
                pasteHTML({json.dumps(html)}, {json.dumps(True)});
            }})();''')
        else: # Ugly hack below to paste into entire content and have at least one undo step
            editor.web.eval(f'''(function () {{
                let nd = document.activeElement.shadowRoot.querySelector('anki-editable');
                if (nd.firstChild && nd.firstChild.nodeName.toLowerCase() !== '#text') {{
                    nd.innerHTML = '<br>' + nd.innerHTML + '<br>';
                }} 
                document.execCommand('selectAll');
                document.execCommand('delete', false);
                pasteHTML({json.dumps(html)}, {json.dumps(True)});
            }})();''')


    # Get content to edit
    if CFG[CFG_SELECTION]:
        # Extend selection to complete lines and use this
        editor.web.evalWithCallback('''(function () {
            let sel = document.activeElement.shadowRoot.getSelection();
            let rng = sel.getRangeAt(0);
            let com_anc = rng.commonAncestorContainer;

            let nd = rng.startContainer;
            if (nd != com_anc) { while (nd.parentNode != com_anc) { nd = nd.parentNode; } }
            if (nd.previousSibling) {{ rng.setStartAfter(nd.previousSibling); }}
            else {{ rng.setStartBefore(nd); }}
            
            nd = rng.endContainer;
            if (nd != com_anc) { while (nd.parentNode != com_anc) { nd = nd.parentNode; } }
            if (nd.nextSibling) {{ rng.setEndBefore(nd.nextSibling); }}
            else {{ rng.setEndAfter(nd); }}
            
            sel.removeAllRanges();
            sel.addRange(rng);
            let tmp = document.createElement('div');
            tmp.append(rng.cloneContents());
            return tmp.innerHTML;
        })();
        ''', run_dlg)
    else:
        # Use entire content
        editor.web.evalWithCallback('''(function () {
            return document.activeElement.shadowRoot.activeElement.innerHTML;
        })();''', run_dlg)


###########################################################################
# Parse config and add shortcuts
###########################################################################
def register_shortcuts(scuts, editor):
    scuts.append([CFG[CFG_OPEN], lambda: input_md(editor, CFG)])


###########################################################################
# Context menu activation - build and append menu items
###########################################################################
def mouse_context(weditor, menu):
    action = QAction(CFG_OPEN)
    action.setShortcut(CFG[CFG_OPEN])
    action.triggered.connect(lambda: input_md(weditor.editor, CFG))
    menu.addAction(action)


###########################################################################
# "Main" - load config and set up hooks
###########################################################################
CFG = mw.addonManager.getConfig(__name__)
CFG[CFG_SELECTION] = CFG.get(CFG_SELECTION) == 'true'
if CFG.get(CFG_OPEN):
    CFG[CFG_OPEN] = QKeySequence(re.sub(r'(?<!_)+', r'|', CFG[CFG_OPEN]))
else:
    CFG[CFG_OPEN] = QKeySequence('Ctrl|M')
if not CFG.get(CFG_INSERT):
    CFG[CFG_INSERT] = 'Ctrl+Enter'
if not CFG.get(CFG_INSERT_PREVIEW):
    CFG[CFG_INSERT_PREVIEW] = 'Ctrl+Shift+Enter'
if not CFG.get(CFG_ELEMENT_CLASS):
    CFG[CFG_ELEMENT_CLASS] = 'md_table'
if not CFG.get(CFG_SIZE_MODE):
    CFG[CFG_SIZE_MODE] = 'parent'
if not CFG.get(CFG_EDITOR_CSS):
    CFG[CFG_EDITOR_CSS] = '.cm-content { font-family: Arial, monospace; font-size: 12px; }'

gui_hooks.editor_did_init_shortcuts.append(register_shortcuts)
addHook('EditorWebView.contextMenuEvent', mouse_context) # Legacy hook but it does fire
#gui_hooks.editor_will_show_context_menu.append(mouse_context) # New style hooks doesn't fire until Image Occlusion Enhanced is fixed
