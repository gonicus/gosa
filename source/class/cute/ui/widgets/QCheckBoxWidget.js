qx.Class.define("cute.ui.widgets.QCheckBoxWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    this._chkBoxWidget = new qx.ui.form.CheckBox();
    this.add(this._chkBoxWidget);

    this._chkBoxWidget.addListener("appear", function(){
        this._chkBoxWidget.addListener("changeValue", function(){
          this.getValue().removeAll();
          this.getValue().push(this._chkBoxWidget.getValue());
          this.fireDataEvent("changeValue", this.getValue().copy());
        }, this);
      }, this);

    this.bind("valid", this._chkBoxWidget, "valid");
    this.bind("invalidMessage", this._chkBoxWidget, "invalidMessage");
  },

  properties: {

    label : {
      init : "",
      check : "String",
      event : "_labelChanged",
      apply : "_applyLabel"
    }
  },

  destruct : function(){
    this._disposeObjects("_chkBoxWidget");
  },


  members: {

    _chkBoxWidget: null,

    _applyLabel : function(value, old_value) {
        this._chkBoxWidget.setLabel(this.tr(value));
    },

    /* Apply method for the value property.
     * This method will regenerate the gui.
     * */
    _applyValue: function(value, old_value){

      if(value && value.length){
        this._chkBoxWidget.setValue(value.getItem(0) == true);
      }
    },

    _applyGuiProperties: function(props){
      if(props["text"] && props["text"]["string"]){
        this.setLabel(props["text"]["string"]);
      }
    },

    focus: function(){
      this._chkBoxWidget.focus();
    }
  }
});
