import sys, os, codecs
import json
from typing import Dict
from anki.hooks import addHook
from aqt import mw, gui_hooks
from aqt.utils import *
from aqt.qt import QMenu, QKeySequence, QApplication, QClipboard

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

        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Return), self).activated.connect(self.accept)
        QShortcut(QKeySequence(Qt.SHIFT + Qt.Key_Escape), self).activated.connect(self.reject)

        self.ui.btns.accepted.connect(self.accept)
        self.ui.btns.rejected.connect(self.reject)

        # Note: when rebuilding of editor.bundle.js you must set the anon function to return the final new EditView to var imd_editor as well as set the doc of the EventState to imd_content

        if html: # htmlmin does not handle NoneType string gracefully
            html = htmlmin.minify(html, remove_all_empty_space=True, keep_pre=True)
            html = re.sub(r'[ ]*<br>[ ]*', r'<br>', html, flags=re.IGNORECASE)
            html = re.sub(r'((<(b|u|i|del|sup|sub|h\d)([ ][^>]*)?>)+)<br>', r'<br>\1', html, flags=re.IGNORECASE)
            html = re.sub(r'<br>((<\/(b|u|i|del|sup|sub|h\d)([][^>]*)?>)+)', r'\1<br>', html, flags=re.IGNORECASE)
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
            <link rel=stylesheet href="codemirror/styles.css">
            <script src="CodeMirror/editor.bundle.js"></script>
        </head>
        <body>
            <script>
                var sd_converter = new showdown.Converter({{extensions: [
                    "extendedTables",
                    "superscript"
                ]}});
                sd_converter.setFlavor('github');
                sd_converter.setOption('underline', 'true');
                sd_converter.setOption('strikethrough', 'true');
                sd_converter.setOption('simpleLineBreaks', 'true');
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
            self.on_accept(html)

        if self.on_accept:
            self.ui.web.page().runJavaScript('''(function () {
                return sd_converter.makeHtml(imd_editor.state.doc.toString());
            })();''', cleanup)
        return super().accept()

    ###########################################################################
    # Main dialog reject
    ###########################################################################
    def reject(self):
        QDialog.reject(self) 


###########################################################################
# Open markdown dialog
###########################################################################
def input_md(editor, CFG):
    # Run the md editor dialog with callback for accept
    def run_dlg(html):
        dlg = IM_dialog(html, editor.parentWindow, dlg_result)
        dlg.show()
    
    # Callback for accepted md dialog
    def dlg_result(html):
        editor.web.eval(f'''
            {"" if CFG[CFG_SELECTION] else "document.execCommand('delete', false, '');"}
            pasteHTML({json.dumps(html)}, {json.dumps(True)});
        ''')

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
            let root = document.activeElement.shadowRoot;
            let sel = root.getSelection();
            let rng = document.createRange();
            rng.selectNodeContents(root.activeElement);
            sel.removeAllRanges();
            sel.addRange(rng);
            return root.activeElement.innerHTML;
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
    menu.addAction(CFG_OPEN, lambda: input_md(weditor.editor, CFG), CFG[CFG_OPEN])


###########################################################################
# "Main" - load config and set up hooks
###########################################################################
CFG = mw.addonManager.getConfig(__name__)
CFG[CFG_SELECTION] = True if not CFG.get(CFG_SELECTION) or CFG.get(CFG_SELECTION).lower() == 'true' else False
if not CFG.get(CFG_OPEN):
    CFG[CFG_OPEN] = 'Ctrl+M'
if not CFG.get(CFG_INSERT):
    CFG[CFG_INSERT] = 'Ctrl+Enter'
if not CFG.get(CFG_INSERT_PREVIEW):
    CFG[CFG_INSERT_PREVIEW] = 'Ctrl+Shift+Enter'
if not CFG.get(CFG_ELEMENT_CLASS):
    CFG[CFG_ELEMENT_CLASS] = 'md_table'

gui_hooks.editor_did_init_shortcuts.append(register_shortcuts)
addHook('EditorWebView.contextMenuEvent', mouse_context) # Legacy hook but it does fire
#gui_hooks.editor_will_show_context_menu.append(mouse_context) # New style hooks doesn't fire until Image Occlusion Enhanced is fixed
