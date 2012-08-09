qx.Class.define("cute.ui.widgets.QSpinBoxWidget", {

  extend: cute.ui.widgets.MultiEditWidget,

  properties: {
  
    maximum: {
      check : "Number",
      init : 100000,
      event: "changeMaximum"
    },

    minimum: {
      check : "Number",
      init : 0,
      event: "changeMinimum"
    }
  },

  members: {
 
    default_value: 0,

    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function(){
      var w = new cute.ui.form.Spinner();
      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }
      w.addListener("changeValue", function(){
          this.addState("modified");
          this._propertyUpdater();
        }, this); 
      this.bind("maximum", w, "maximum");
      this.bind("minimum", w, "minimum");
      return(w);
    }
  }
});
