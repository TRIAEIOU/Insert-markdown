import {KeyBinding, Command} from "@codemirror/view";
import {TransactionSpec, Extension} from '@codemirror/state';

// Keep track of ordinal
export class ordinal {
    static current = 0;
}

// Wrap selection(s) in cloze tags
const clozeSelections = (inc: boolean): Command => (view) => {
    const selection = view.state.selection;
    let trs: TransactionSpec[] = [];
    for (const r of selection.ranges) {
        if (inc) { ordinal.current++; }
        if (r.empty) {
            trs.push({changes: {from: r.from, to: r.from, insert: `{{c${ordinal.current || 1}::}}`}});
        } else {
            trs.push({changes: {from: r.from, to: r.from, insert: `{{c${ordinal.current || 1}::`}});
            trs.push({changes: {from: r.to, to: r.to, insert: '}}'}});
        }
    }
    view.dispatch(...trs);
    return true;
  };

// Public functions 
export const clozeNext = clozeSelections(true);
export const clozeCurrent = clozeSelections(false);

// Keyboard shortcuts
export const ankiClozeKeymap: ReadonlyArray<KeyBinding> = [
    { key: 'Ctrl-Shift-c', run: clozeNext },
    { key: 'Ctrl-Alt-c', run: clozeCurrent }
]

// Create extension with current ordinal
export function ankiCloze(options: {ordinal?: number} = {}): Extension {
    ordinal.current = options.ordinal == null ? 0 : options.ordinal;
    return []
  }
