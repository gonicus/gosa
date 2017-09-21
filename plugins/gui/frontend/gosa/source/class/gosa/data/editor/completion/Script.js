/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/**
 * Completion provider for shell scripts. Only provides completion for shebang line
 *
 * @ignore(monaco.*)
 */
qx.Class.define("gosa.data.editor.completion.Script", {
  extend: qx.core.Object,
  implement: gosa.data.editor.completion.IProvider,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(object) {
    this.base(arguments);
    this._object = object;
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    _object: null,
    _language: null,

    getProvider: function(lang) {
      // as monaco is currently not supporting bash those scripts were treated as plaintext
      switch (lang) {
        case "plaintext":
        case "bash":
          return {
            triggerCharacters: ["#"],
            provideCompletionItems: this.provideCompletionItems.bind(this)
          };

        case "python":
          return {
            triggerCharacters: ["#"],
            provideCompletionItems: this.provideCompletionItems.bind(this)
          };
      }
    },

    provideShebang: function(res) {
      res.push({
        label : "python",
        insertText : "!/usr/bin/env python\n\n",
        kind : monaco.languages.CompletionItemKind.Text
      });
      res.push({
        label : "bash",
        insertText : "!/bin/bash\n\n",
        kind : monaco.languages.CompletionItemKind.Text
      });
      return res;
    },

    provideCompletionItems: function(model, position) {
      var res = [];
      var textUntilPosition = model.getValueInRange({
        startLineNumber : position.lineNumber,
        startColumn : 1,
        endLineNumber : position.lineNumber,
        endColumn : position.column
      });
      var lastWord = textUntilPosition.split(" ").pop();

      if (lastWord.startsWith("#") && position.lineNumber === 1) {
        // shebang suggestion
        return this.provideShebang(res);
      }
      return res;
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._object = null;
  }
});