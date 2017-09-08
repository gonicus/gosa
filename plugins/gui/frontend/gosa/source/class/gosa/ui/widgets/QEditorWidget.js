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
 * Widget with an text editor with syntax highlighting, code-completion and other fancy features.
 * Embeds the Monaco Editor {@link https://microsoft.github.io/monaco-editor/index.html}
 *
 * @ignore(require.*,monaco.*)
 */
qx.Class.define("gosa.ui.widgets.QEditorWidget", {

  extend: gosa.ui.widgets.MultiEditWidget,

  construct: function(){
    this.base(arguments);

    var monacoPath = "gosa/js/monaco-editor/"+(qx.core.Environment.get("qx.debug") ? "dev/vs" : "min/vs");
    var dynLoader = new qx.util.DynamicScriptLoader([
      monacoPath+"/loader.js"
    ]);
    var parts = qx.util.ResourceManager.getInstance().toUri(monacoPath+"/loader.js").split("/");
    parts.pop();

    dynLoader.addListenerOnce('ready',function() {
      this.debug("monaco editor has been loaded!");
      this.__loaded = true;
      require.config({
        paths: { 'vs': parts.join("/") },
        "vs/nls" : { availableLanguages: { "*": qx.locale.Manager.getInstance().getLocale() }}
      });
      this._generateGui();
    }, this);


    dynLoader.addListener('failed',function(e) {
      var data = e.getData();
      this.error("failed to load "+data.script);
    }, this);

    dynLoader.start();
  },

  statics: {
    
    /**
     * Create a readonly representation of this widget for the given value.
     * This is used while merging object properties.
     */
    getMergeWidget: function(value){
      // var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      // for(var i=0;i<value.getLength(); i++){
      //   var w = new qx.ui.form.TextArea(value.getItem(i));
      //   w.setReadOnly(true);
      //   container.add(w);
      // }
      // return(container);
    }
  },

  members: {
    _default_value: "",
    __loaded: false,

    _generateGui: function() {
      if (this.__loaded) {
        this.base(arguments);
      }
    },

    /**
     * Parses an incoming error-object and then sets the error message.
     * @param error_object {Error}
     */
    setError: function(error_object){
      var message = error_object.text;
      if(error_object.details) {
        // collect details for each widget
        var detailsByIndex = {};
        for(var i=0; i< error_object.details.length; i++) {
          if (!detailsByIndex[error_object.details[i].index]) {
            detailsByIndex[error_object.details[i].index] = [];
          }
          detailsByIndex[error_object.details[i].index].push(error_object.details[i]);

        }
        Object.getOwnPropertyNames(detailsByIndex).forEach(function(idx) {
          this.setErrorMessage(detailsByIndex[idx], parseInt(idx));
        }, this);

      } else {
        this.setErrorMessage(message, 0);
      }
    },


    /**
     * Sets an error message for this widgets
     */
    setErrorMessage: function(message, id){
      var w = this._getWidget(id);
      w.setInvalidMessage(message);
      w.setValid(false);
      this.setValid(false);
    },

    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function() {
      var w = new gosa.ui.editor.Monaco();

      w.addListener("focusout", this._propertyUpdater, this);
      w.addListener("changeValue", this._propertyUpdaterTimed, this);
      this.bind("valid", w, "valid");
      this.bind("invalidMessage", w, "invalidMessage");
      this.bind("guiProperties", w, "guiProperties");
      this.bind("height", w, "height");
      return(w);
    }
  }
});
