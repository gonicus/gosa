qx.Class.define("cute.ui.widgets.QCheckBoxWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    this._chkBoxWidget = new qx.ui.form.CheckBox();
    this.add(this._chkBoxWidget);
    this._chkBoxWidget.addListener("changeValue", function(){
        this.getValue().removeAll();
        this.getValue().push(this._chkBoxWidget.getValue());
        if(this._initialized){
          this.fireDataEvent("changeValue", this.getValue());
        }
      }, this);
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

    _initialized: false,

    _chkBoxWidget: null,

    _applyLabel : function(value, old_value) {
        this._chkBoxWidget.setLabel(this.tr(value));
    },

    /* Apply method for the value property.
     * This method will regenerate the gui.
     * */
    _applyValue: function(value, old_value){

      if(value && value.length){
        this._chkBoxWidget.setValue(value.getItem(0));
        this._initialized = true;
      }
    },

    _applyGuiProperties: function(props){
      if(props["text"] && props["text"]["string"]){
        this.setLabel(props["text"]["string"]);
      }
    },

    setInvalidMessage: function(message){
      this._chkBoxWidget.setInvalidMessage(message);
    },

    resetInvalidMessage: function(){
      this._chkBoxWidget.resetInvalidMessage();
    },

    focus: function(){
      this._chkBoxWidget.focus();
    },

    setValid: function(bool){
      this._chkBoxWidget.setValid(bool);
    }
  }
});
