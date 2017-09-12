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
 * Show a key / value pair as two separate Textfields.
 */
qx.Class.define("gosa.ui.widgets.KeyValueEditWidget", {
  extend: gosa.ui.widgets.MultiEditWidget,

  statics: {

    /**
     * Create a readonly representation of this widget for the given value.
     * This is used while merging object properties.
     */
    getMergeWidget: function(value){
      var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      for(var i=0;i<value.getLength(); i++) {
        var w = new qx.ui.form.TextField(value.getItem(i));
        w.setReadOnly(true);
        container.add(w);
      }
      return(container);
    }
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    separator: {
      check: "String",
      init: ":"
    }
  },

  members: {
    _default_value: "",

    shortcutExecute : function()
    {
      this.focus();
    },

    // overridden (bound to widgets readOnly attribute)
    _applyReadOnly: function() {
    },

    /**
     * Sets an error message for this widgets
     */
    setErrorMessage: function(message, id){
      var w = this._getWidget(id);
      w.getLayoutChildren().forEach(function(child) {
        child.setInvalidMessage(message);
        child.setValid(false);
      });
      this.setValid(false);
    },


    /**
     * Resets the "invalidMessage" string for all widgets.
     */
    resetErrorMessage: function(){
      for(var i=0; i < this._current_length; i++){
        this._getWidget(i).getLayoutChildren().forEach(function(child) {
          child.resetInvalidMessage();
          child.setValid(true);
        });
      }
      this.setValid(true);
    },

    _getWidgetValue: function(id) {
      var container = this._getWidget(id);
      var data = [container.getLayoutChildren()[0].getValue(), container.getLayoutChildren()[1].getValue()]
      return data.join(this.getSeparator())
    },

    _setWidgetValue: function(id, value){
      try{
        if (value && qx.Class.implementsInterface(value, gosa.io.types.IType)) {
          value = value.toString();
        }
        var container = this._getWidget(id);
        if (!value) {
          container.getLayoutChildren()[0].setValue("");
          container.getLayoutChildren()[1].setValue("");
          return;
        }
        var parts = value.split(this.getSeparator());
        if (parts.length > 0) {
          container.getLayoutChildren()[0].setValue(parts.shift());
        }
        if (parts.length > 0) {
          container.getLayoutChildren()[1].setValue(parts.join(this.getSeparator()));
        }
      } catch(e){
        this.error("failed to set widget value for " + this.getAttribute() + ". "+ e);
      }
    },

    _applyValid : function(value, old, name) {
      if (value) {
        this.removeState("invalid");
      }
      else {
        this.addState("invalid");
      }

      // forward valid state to "real" widget children
      Object.getOwnPropertyNames(this._widgetContainer).forEach(function(id) {
        this._widgetContainer[id].getWidget().getLayoutChildren().forEach(function(child) {
          child.setValid(value);
          child.setInvalidMessage(this.getInvalidMessage());
        }, this);
      }, this);
    },

    focus: function(){
      if(Object.getOwnPropertyNames(this._widgetContainer).length){
        this._widgetContainer[0].getWidget().getLayoutChildren()[0].focus();
      }
    },

    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function(){
      var w;

      w = new qx.ui.container.Composite();
      w.setLayout(new qx.ui.layout.HBox(8));

      var key = new qx.ui.form.TextField();
      w.getContentElement().setAttribute("spellcheck", true);
      var value = new qx.ui.form.TextField();
      w.getContentElement().setAttribute("spellcheck", true);

      this.bind("readOnly", key, "readOnly");
      this.bind("readOnly", value, "readOnly");

      if(this.getMaxLength()){
        key.setMaxLength(this.getMaxLength());
        value.setMaxLength(this.getMaxLength());
      }

      key.setLiveUpdate(true);
      key.addListener("focusout", this._propertyUpdater, this);
      key.addListener("changeValue", this._propertyUpdaterTimed, this);
      value.setLiveUpdate(true);
      value.addListener("focusout", this._propertyUpdater, this);
      value.addListener("changeValue", this._propertyUpdaterTimed, this);
      w.add(key, {flex: 1});
      w.add(value, {flex: 2});
      return(w);
    }
  }
});
