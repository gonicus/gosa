qx.Class.define("cute.ui.widgets.QDateTimeEditWidget", {

  extend : cute.ui.widgets.MultiEditWidget,

  members: {
 
    _default_value: null,
    

    /* Returns the value from the widget given by its id
     * */
    _getWidgetValue: function(id){
      var value = this._getWidget(id).getValue();
      if(value){
        return(new cute.io.types.Timestamp(value));
      }else{
        return(null);
      }
    },


    /* Set a new value for the widget given by id.
     * */
    _setWidgetValue: function(id, value){
      var w = this._getWidget(id);
      if(this.getValue().getItem(id)){
        w.setValue(this.getValue().getItem(id).get());
      }else{
        w.setValue(null);
      }
    },


    /* Creates an input-widget and connects the update listeners
     * */
    _createWidget: function(){
      var w = new qx.ui.form.DateField();
      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }
      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }
      w.addListener("changeValue", function(){
          this.addState("modified");
          this._propertyUpdater();
        }, this);
      this.bind("valid", w, "valid");
      this.bind("invalidMessage", w, "invalidMessage");
      return(w);
    }
  }
});
