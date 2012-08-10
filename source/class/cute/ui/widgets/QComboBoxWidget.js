qx.Class.define("cute.ui.widgets.QComboBoxWidget", {

  extend: cute.ui.widgets.MultiEditWidget,

  members: {
 
    default_value: "",


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
      var selection = this.id2item(this.getValues(), value);
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

      ////TODO: re-enable
      //var theme = "default";
      //if (cute.Config.theme) {
      //    theme = cute.Config.theme;
      //}
      //// create the options for the icon
      //var iconOptions = {
      //  converter: function(value) {
      //    return "cute/themes/" + theme + "/" + value;
      //  }
      //};

      //controller.setIconPath('icon');
      //controller.setIconOptions(iconOptions);
      controller.getSelection().addListener("change", function(){
          this.addState("modified");
          this._propertyUpdater();
        }, this);

      return(w);
    },

    _applyValues: function(data){

      if(data.classname != "qx.data.Array"){
        var items = [];

        if(!this.getMandatory()){
          var item = new cute.data.model.SelectBoxItem();
          item.setValue("");
          item.setKey(null);
          items.push(item);
        }

        if (qx.Bootstrap.getClass(data) == "Object") {
          for (var k in data) {
            var item = new cute.data.model.SelectBoxItem();
            item.setKey(k);
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
            var item = new cute.data.model.SelectBoxItem();
            item.setValue(data[k]);
            item.setKey(data[k]);
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
