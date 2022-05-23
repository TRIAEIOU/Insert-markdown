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
    for (const r of selection.ranges) {
        if (inc) { i++; }
        if (r.empty) {
            trs.push({changes: {from: r.from, to: r.from, insert: `{{c${i || 1}::}}`}});
        } else {
            trs.push({changes: {from: r.from, to: r.from, insert: `{{c${i || 1}::`}});
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
export const ankiClozeKeymap = [
    { key: 'Ctrl-Shift-c', run: clozeNext },
    { key: 'Ctrl-Alt-c', run: clozeCurrent }
]

// Create extension with current ordinal
export function ankiCloze(options = {}) {
    Ordinal.base = options['ordinal'] === undefined ? 0 : options['ordinal'];
    return []
  }
