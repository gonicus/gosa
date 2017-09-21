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
    appearance: {
      refine: true,
      init: "textfield"
    },

    editor: {
      check: "Object",
      init: null,
      apply: "_applyEditor"
    },

    valid: {
      check: "Boolean",
      init: true,
      apply: "_applyValid"
    },

    invalidMessage: {
      init: "",
      apply: "_applyInvalidMessage"
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
    },
    completionProviders: {
      check: "Object",
      nullable: true,
      apply: "_applyCompletionProviders"
    }
  },

  members : {
    _skipApply: false,
    __currentLanguage: null,
    __currentLanguageVersion: null,
    __monaco: null,

    __disableTab: function(ev) {
      if (ev.getKeyIdentifier() === "Tab") {
        ev.stopPropagation();
        ev.preventDefault();
      }
    },

    _applyCompletionProviders: function(value) {
      if (this.__monaco && value) {
        Object.getOwnPropertyNames(value).forEach(function(lang) {
          this.debug("registering completion provider for language: "+lang);
          monaco.languages.registerCompletionItemProvider(lang, value[lang]);
        }, this);
      }
    },

    _init: function() {
      var element = this.getContentElement().getDomElement();
      element.setAttribute("tabIndex", "-1");

      require(['vs/editor/editor.main'], function() {
        this.__monaco = monaco;
        this._applyCompletionProviders(this.getCompletionProviders());

        monaco.languages.setLanguageConfiguration('python', {
          onEnterRules: [
            {
              beforeText: /.*/,
              action: {
                appendText: '\n'
              }
            }
          ]
        });

        var config = qx.lang.Object.mergeWith({
          value : this.getValue(),
          language : 'python',
          autoIndent: true,
          folding: true
        }, this.getGuiProperties() || {});

        var editor = monaco.editor.create(element, config);
        this.setEditor(editor);

        editor.onDidFocusEditor(this._onFocus.bind(this));
        editor.onDidBlurEditor(this._onBlur.bind(this));
      }.bind(this));
    },

    _onFocus: function() {
      if (!this.__lid) {
        this.__lid = qx.core.Init.getApplication().getRoot().addListener("keypress", this.__disableTab, this, true);
      }
      gosa.ui.command.GroupManager.getInstance().block();
    },

    _onBlur: function() {
      if (this.__lid) {
        qx.core.Init.getApplication().getRoot().removeListenerById(this.__lid);
        this.__lid = null;
      }
      gosa.ui.command.GroupManager.getInstance().unblock();
    },


    _applyInvalidMessage: function(value) {
      if (qx.lang.Type.isArray(value)) {
        var markers = [];
        value.forEach(function(error) {
          markers.push({
            severity: monaco.Severity.Error,
            startLineNumber: error.line,
            startColumn: error.column,
            endLineNumber: error.line,
            endColumn: error.column+1,
            message: error.message
          });
        }, this);
        this.__monaco.editor.setModelMarkers(this.getEditor().getModel(), '', markers);
      }
    },

    _applyValid: function(value) {
      if (this.__monaco) {
        this.__monaco.editor.setModelMarkers(this.getEditor().getModel(), '', []);
      }
      if (value) {
        this.removeState("invalid");
      }
      else {
        this.addState("invalid");
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
      var firstLine = content || this.getEditor().getModel().getLineContent(1);
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
            this.__currentLanguage = "bash";
            this.__currentLanguageVersion = null;
            return "bash";
          case "python3":
          case "python2":
          case "python":
            this.__currentLanguage = "python";
            var versionMatch = /^python([\d]?)$/.exec(binary);
            if (versionMatch) {
              this.__currentLanguageVersion = parseInt(versionMatch[1]);
            } else {
              // default is python2
              this.__currentLanguageVersion = 2;
            }
            return "python";
          default:
            this.__currentLanguageVersion = null;
            this.__currentLanguage = null;
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