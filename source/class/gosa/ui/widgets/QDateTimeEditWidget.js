qx.Class.define("gosa.ui.widgets.QDateTimeEditWidget", {

  extend : gosa.ui.widgets.QDateEditWidget,

  members: {
 
    /* Creates an input-widget and connects the update listeners
     * */
    _createWidget: function(){
      var w = new gosa.ui.widgets.DateTimeField();

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
