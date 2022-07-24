import {KeyBinding, Command} from "@codemirror/view";
import {TransactionSpec, Extension} from '@codemirror/state';

// Keep track of ordinal
export class Ordinal {
    static base = 0;
}

// Wrap selection(s) in cloze tags
const clozeSelections = (inc) => (view) => {
    const selection = view.state.selection;
    let i = Ordinal.base;
    let itr = view.state.doc.iter();
    while (!itr.done) {
        if (!itr.lineBreak) {
            for(const match of itr.value.matchAll(/{{c(\d+)::/g)) {
                const n = parseInt(match[1]);
                if (n > i) { i = n; }
            }
        }
        itr.next();
    }

    let trs = [];
    let cloze_lengths = 0;
    let last_pos = null;
    for (const r of selection.ranges) {
        if (inc) { i++; }
        let copen = `{{c${i || 1}::`;
        cloze_lengths += copen.length + 2;
        if (r.empty) {
            last_pos =  r.anchor + cloze_lengths - 2; // Inside empty cloze
            trs.push({changes: {from: r.from, to: r.from, insert: copen + '}}'}});
        } else {
            last_pos = r.to + cloze_lengths; // After populated cloze
            trs.push({changes: {from: r.from, to: r.from, insert: copen}});
            trs.push({changes: {from: r.to, to: r.to, insert: '}}'}});
        }
    }
    view.dispatch(...trs);
    if (cloze_lengths !== null) { view.dispatch({selection: {anchor: last_pos}}); }
    return true;
  };

// Public functions 
export const clozeNext = clozeSelections(true);
export const clozeCurrent = clozeSelections(false);

// Keyboard shortcuts
export const ankiClozeKeymap = [
    { key: 'Ctrl-Shift-c', run: clozeNext },
    { key: 'Ctrl-Alt-c', run: clozeCurrent }
]

// Create extension with current ordinal
export function ankiCloze(options = {}) {
    Ordinal.base = options['ordinal'] === undefined ? 0 : options['ordinal'];
    return []
  }
