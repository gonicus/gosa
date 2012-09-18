qx.Class.define("cute.ui.widgets.QDateTimeEditWidget", {

  extend : cute.ui.widgets.QDateEditWidget

  members: {
 
    /* Creates an input-widget and connects the update listeners
     * */
    _createWidget: function(){
      var w = new qx.ui.form.DateField();
      var format = new qx.util.format.DateFormat("dd.MM.yyyy HH:mm:ss");
      w.setWidth(160);
      w.setDateFormat(format);

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
