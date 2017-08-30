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

qx.Class.define("gosa.ui.widgets.QComboBoxWidget", {

  extend: gosa.ui.widgets.MultiEditWidget,

  construct: function(){
    this.base(arguments);

    this.addListenerOnce("initCompleteChanged", function(){
      if (this._use_default && !this.isBlocked()) {
        this.addState("modified");
        this._propertyUpdater();
      }
    }, this);
  },

  properties: {

    model: {
      event: "modelChanged",
      nullable: true,
      init: null
    },

    sortBy: {
      check: ["key", "value"],
      nullable: true
    },

    delegate: {
      check: "Object",
      init: {},
      event: "changeDelegate"
    }
  },

  statics: {

    /* Create a readonly representation of this widget for the given value.
     * This is used while merging object properties.
     * */
    getMergeWidget: function(value){
      var w = new qx.ui.form.TextField();
      w.setReadOnly(true);
      if(value.getLength()){
        w.setValue(value.getItem(0) + "");
      }
      return(w);
    }
  },

  members: {

    _was_initialized: false,
    _model_initialized: false,
    _default_value: null,
    _use_default: false,


    /* Returns the value from the widget given by its id
     * */
    _getWidgetValue: function(id){
      var value = null;
      if(this._getWidget(id).getSelection().length){
        value = this._getWidget(id).getSelection().getItem(0).getKey();
      }
      return(value);
    },

    setWidgetValue : function(id, value) {
      this._setWidgetValue(id, value);
    },

    /* Set a new value for the widget given by id.
     * */
    _setWidgetValue: function(id, value){

      // Find model item with appropriate key
      var w = this._getWidget(id);
      var modelItem = null;
      w.getModel().some(function(item) {
        if (item.getKey() == value) {
          modelItem = item;
          return true;
        }
      });
      w.getSelection().replace([modelItem]);
    },


    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function(id) {
      var w = new qx.ui.form.VirtualSelectBox();
      this.bind("delegate", w, "delegate");
      w.set({
        labelPath: "value",
        iconPath: "icon"
      });

      if (this.getModel() !== null) {
        w.setModel(this.getModel());
      }
      this.addListener("modelChanged", function() {
        if (this.getModel() !== null) {
          w.setModel(this.getModel());
        }
      }, this);

      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }
      w.getSelection().addListener("change", function(){

        if(this.isMandatory() && this.getValue().getItem(id) === this._default_value && this._getWidgetValue(id)){
          this._use_default = true;
        }

        if(this._model_initialized){
          this.addState("modified");
          this._propertyUpdater();
        }
      }, this);

      this.bind("valid", w, "valid");
      this.bind("invalidMessage", w, "invalidMessage");
      return(w);
    },


    /* Apply the widget values - fills the combobox selectables.
     * */
    _applyValues: function(data){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(!data){
        return;
      }

      var convert, item, k;

      if (this.getType() === "Integer") {
        convert = function(value) {
          var res = parseInt(value);
          if(isNaN(res)) {
            this.error("failed to convert ComboBox value "+value+" to int ("+this.getExtension()+"."+this.getAttribute()+")");
            return(0);
          }
          else {
            return(res);
          }
        }.bind(this);
      }
      else if (this.getType() === "Boolean"){
        convert = function(value) {
          return value.toLowerCase() === "true";
        };
      }
      else{
        convert = function(value) {
          return value;
        };
      }
      if(data.classname !== "qx.data.Array"){
        var items = [];

        if(!this.getMandatory()){
          item = new gosa.data.model.SelectBoxItem();
          item.setValue("");
          item.setKey(null);
          items.push(item);
        }

        if (qx.Bootstrap.getClass(data) === "Object") {
          for (k in data) {
            item = new gosa.data.model.SelectBoxItem();
            item.setKey(convert(k));
            if (data[k] && data[k]['value']) {
              item.setValue(data[k]['value']);
              if (data[k]['icon']) {
                item.setIcon(data[k]['icon']);
              }
            } else {
              item.setValue(data[k] || "");
            }
            items.push(item);
          }
        } else {
          for (k = 0; k < data.length; k++) {
            item = new gosa.data.model.SelectBoxItem();
            item.setValue(data[k]);
            item.setKey(convert(data[k]));
            items.push(item);
          }
        }
        var delegate = {};
        if (this.getSortBy() === "key") {
          delegate.sorter = function(a,b) {
            return a.getKey().localeCompare(b.getKey());
          };
        } else if (this.getSortBy() === "value") {
          delegate.sorter = function(a,b) {
            return a.getValue().localeCompare(b.getValue());
          };
        }
        this.setDelegate(delegate);
        this.setModel(new qx.data.Array(items));
        this._model_initialized = true;
      }
    },


    id2item : function(values, selected) {
      if (values) {
        for (var i = 0; i<values.length; i++) {
          if (values.getItem(i).getKey() === selected) {
            return values.getItem(i);
          }
        }
      }
      return null;
    }
  }
});
