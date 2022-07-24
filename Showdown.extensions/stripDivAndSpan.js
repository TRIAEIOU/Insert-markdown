/*******************************************************************
 * Strip div and span tags, retaining interior
 */
(function (extension) {
  'use strict';
  // Boiler plate loader code
  if (typeof showdown !== 'undefined') {
    extension(showdown);
  } else if (typeof define === 'function' && define.amd) {
    define(['showdown'], extension);
  } else if (typeof exports === 'object') {
    module.exports = extension(require('showdown'));
  } else {
    throw Error('Could not find showdown library');
  }
}(function (showdown) {
  'use strict';

  /*********************************************************************
   * Strip divs and spans inside a table
   * naming confusion
   * @param {Event} evt evt: Recieved Event object
   * @return {Event} Event object with final output
   */
  function stripDivAndSpan(evt) {
    if (evt.input.nodeName === 'DIV' || evt.input.nodeName === 'SPAN') {
      evt.output = '';
      evt.input.childNodes.forEach(nd => {
        evt.output += showdown.subParser('makeMarkdown.node')(nd, evt.globals, evt.spansOnly);
      });
      if (evt.input.nodeName === 'DIV') { evt.output = `  \n${evt.output}  \n`; }
    }
    return evt;
  }

  /*******************************************************************
   * Register extension
   */
  showdown.extension('stripDivAndSpan', function () {
    'use strict';
    return {
      type: 'listener',
      listeners: {
        "makemarkdown.unhandledNode": stripDivAndSpan
      }
    };
  });
}));