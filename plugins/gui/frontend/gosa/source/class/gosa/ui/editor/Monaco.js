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
 * Wrapper for Monaco IStandaloneCodeEditor instance
 *
 * @ignore(require.*,monaco.*)
 */
qx.Class.define("gosa.ui.editor.Monaco", {
  extend : qx.ui.core.Widget,
  implement: qx.ui.form.IStringForm,
  
  construct : function(path) {
    this.base(arguments);
    this.addListenerOnce("appear", this._init, this);

    this.__debouncedSendValue = new qx.util.Function.debounce(function() {
      this.fireDataEvent("changeValue", this.getValue());
    }.bind(this), 1000);
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "changeValue": "qx.event.type.Data"
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    editor: {
      check: "Object",
      init: null,
      apply: "_applyEditor"
    },

    valid: {
      check: "Boolean",
      init: true
    },

    invalidMessage: {
      check: "String",
      init: ""
    },
    guiProperties: {
      apply: "_applyGuiProperties",
      event: "_guiPropertiesChanged",
      init: null,
      nullable: true
    },
    value: {
      check: "String",
      init: "null",
      apply: "_applyValue"
    }
  },

  members : {
    _skipApply: false,

    __disableTab: function(ev) {
      if (ev.getKeyIdentifier() === "Tab" || ev.getKeyIdentifier() === "Enter") {
        ev.stopPropagation();
        ev.preventDefault();
      }
    },

    _init: function() {
      var element = this.getContentElement().getDomElement();
      element.setAttribute("tabIndex", "-1");

      require(['vs/editor/editor.main'], function() {

        monaco.languages.setLanguageConfiguration('python', {
          onEnterRules: [
            {
              action: { appendText: '\n' }
            }
          ]
        });

        var config = qx.lang.Object.mergeWith({
          value : this.getValue(),
          language : 'python',
          autoIndent: true,
          acceptSuggestionOnEnter: "off"
        }, this.getGuiProperties() || {});
        console.log(config);
        var editor = monaco.editor.create(element, config);
        this.setEditor(editor);

        editor.onDidFocusEditor(this._onFocus.bind(this));
        editor.onDidBlurEditor(this._onBlur.bind(this));
      }.bind(this));
    },

    _onFocus: function() {
      if (!this.__lid) {
        console.log(this.toHashCode()+" add key listener");
        this.__lid = qx.core.Init.getApplication().getRoot().addListener("keypress", this.__disableTab, this, true);
      }
    },

    _onBlur: function() {
      if (this.__lid) {
        console.log(this.toHashCode()+" remove key listener");
        qx.core.Init.getApplication().getRoot().removeListenerById(this.__lid);
        this.__lid = null;
      }
    },

    //property apply
    _applyGuiProperties: function(value) {
      if (this.getEditor()) {
        this.getEditor().updateOptions(value);
      }
    },

    // property apply
    _applyValue: function(value) {
      if (this.getEditor() && this._skipApply === false) {
        this.getEditor().setValue(value);
      }
    },

    //property apply
    _applyEditor: function(value, old) {
      if (old) {
        old.dispose();
      }
      value.onDidChangeModelContent(this.__onModelContentChange.bind(this));
    },

    __checkContentLanguage: function(content) {
      var firstLine = content || this.getEditor().getValue().split("\n")[0];
      monaco.editor.setModelLanguage(this.getEditor().getModel(), this.__detectLanguage(firstLine));
    },

    __detectLanguage: function(shebang) {
      // test env
      var match = /#!\/(usr\/)?bin\/([^\s]+)\s?(.+)?/.exec(shebang);
      if (match) {
        var binary = match[2] === "env" ? match[3] : match[2];
        switch (binary) {
          case "sh":
          case "zsh":
          case "csh":
          case "bash":
            return "bash";
          case "python":
          case "python2":
          case "python3":
            return "python";
          default:
            return binary;
        }
      } else {
        // no shebang line, default lang is python
        return "python";
      }
    },

    __onModelContentChange: function(ev) {
      // // check if first line has changes (we night need to update the language
      ev.changes.forEach(function(change) {
        if (change.range.startLineNumber === 1 && change.range.endLineNumber >= 1) {
          this.__checkContentLanguage();
        }
      }, this);
      if (ev.changes.length) {
        this._skipApply = true;
        this.setValue(this.getEditor().getValue());
        this._skipApply = false;
        this.__debouncedSendValue();
      }
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._onBlur();
    var ed = this.getEditor();
    if (ed) {
      ed.dispose();
    }
  }
});