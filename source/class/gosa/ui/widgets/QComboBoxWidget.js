/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.widgets.QComboBoxWidget", {

  extend: gosa.ui.widgets.MultiEditWidget,

  members: {
 
    _default_value: "",


    /* Returns the value from the widget given by its id
     * */
    _getWidgetValue: function(id){
      var value = null;
      if(this._getWidget(id).getSelection()){
        value = this._getWidget(id).getSelection()[0].getModel().getKey();
      }
      return(value);
    },


    /* Set a new value for the widget given by id.
     * */
    _setWidgetValue: function(id, value){

      // Find model item with appropriate key
      var w = this._getWidget(id);
      for(var item in w.getChildren()){
        if(w.getChildren()[item].getModel().getKey() == value){
          w.setSelection([w.getChildren()[item]]);
          break;
        }
      }
    },


    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function(){

      var w = new qx.ui.form.SelectBox();
      var controller = new qx.data.controller.List(this.getValues(), w, "value");

      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }

      // create the options for the icon
      //var iconOptions = {
      //  converter: function(value) {
      //    return gosa.Config.getImagePath(value, 22);
      //  }
      //};

      //controller.setIconPath('icon');
      //controller.setIconOptions(iconOptions);
      controller.getSelection().addListener("change", function(){
          this.addState("modified");
          this._propertyUpdater();
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

      var convert;
    	
      if(this.getType() == "Integer"){
        var that = this;
        convert = function(value){
            var res = parseInt(value);
            if(res == NaN){
              that.error("failed to convert ComboBox value "+value+" to int ("+that.getExtension()+"."+that.getAttribute()+")");
              return(0);
            }else{
              return(res);
            }
          };
      }else if(this.getType() == "Boolean"){
        convert= function(value){
            return(value == "True");
          };
      }else{
        convert= function(value){
            return(value);
          };
      }

      if(data.classname != "qx.data.Array"){
        var items = [];

        if(!this.getMandatory()){
          var item = new gosa.data.model.SelectBoxItem();
          item.setValue("");
          item.setKey(null);
          items.push(item);
        }

        if (qx.Bootstrap.getClass(data) == "Object") {
          for (var k in data) {
            var item = new gosa.data.model.SelectBoxItem();
            item.setKey(convert(k));
            if (data[k]['value']) {
              item.setValue(data[k]['value']);
              item.setIcon(data[k]['icon']);
            } else {
              item.setValue(data[k]);
            }
            items.push(item);
          }
        } else {
          for (var k = 0; k < data.length; k++) {
            var item = new gosa.data.model.SelectBoxItem();
            item.setValue(data[k]);
            item.setKey(convert(data[k]));
            items.push(item);
          }
        }

        this.setValues(new qx.data.Array(items));
      }
    },

    
    id2item : function(values, selected) {
      if (values) {
        for (var i = 0; i<values.length; i++) {
          if (values.getItem(i).getKey() == selected) {
            return values.getItem(i);
          }
        }
      }
      return null;
    }
  }
});
