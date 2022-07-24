import {EditorView, keymap, highlightSpecialChars, drawSelection, highlightActiveLine, dropCursor} from "@codemirror/view"
import {EditorState} from "@codemirror/state"
import {history, historyKeymap} from "@codemirror/history"
import {indentOnInput} from "@codemirror/language"
import {defaultKeymap, indentWithTab} from "@codemirror/commands"
import {bracketMatching} from "@codemirror/matchbrackets"
import {closeBrackets, closeBracketsKeymap} from "@codemirror/closebrackets"
import {searchKeymap, highlightSelectionMatches} from "@codemirror/search"
import {autocompletion, completionKeymap} from "@codemirror/autocomplete"
import {rectangularSelection, crosshairCursor} from "@codemirror/rectangular-selection"
import {search} from "@codemirror/search"
import {defaultHighlightStyle} from "@codemirror/highlight"
import {markdown} from "@codemirror/lang-markdown"
import {ankiCloze, ankiClozeKeymap} from "./ankiCloze/ankiCloze"

export function create(doc, ord) {
  return new EditorView({
    state: EditorState.create({
      doc: doc,
      extensions: [
        highlightSpecialChars(),
        history(),
        drawSelection(),
        dropCursor(),
        EditorState.allowMultipleSelections.of(true),
        indentOnInput(),
        defaultHighlightStyle.fallback,
        bracketMatching(),
        closeBrackets(),
        autocompletion(),
        rectangularSelection(),
        search(),
        crosshairCursor(),
        highlightActiveLine(),
        highlightSelectionMatches(),
        keymap.of([
          ...closeBracketsKeymap,
          ...defaultKeymap,
          ...searchKeymap,
          ...historyKeymap,
          ...completionKeymap,
          indentWithTab,
          ...ankiClozeKeymap
        ]),
        EditorView.lineWrapping,
        markdown(),
        ankiCloze({ordinal: ord})
      ]
    }),
    parent: document.body
  });
}