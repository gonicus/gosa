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
 
    _default_value: 0,

    /* Apply collected gui properties to this widet
     * */
    _applyGuiProperties: function(props){
      if(!props){
        return;
      }
      if(props["placeholderText"] && props["placeholderText"]["string"]){
        this.setPlaceholder(props["placeholderText"]["string"]);
      }
      if(props["maximum"] && props["maximum"]["number"]){
        this.setMaximum(parseInt(props["maximum"]["number"])) ;
      }
      if(props["minimum"] && props["minimum"]["number"]){
        this.setMinimum(parseInt(props["minimum"]["number"])) ;
      }
    },

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
      w.bind("backgroundColor", w.getChildControl("textfield"), "backgroundColor");
      this.bind("valid", w, "valid");
      this.bind("invalidMessage", w, "invalidMessage");
      return(w);
    }
  }
});
