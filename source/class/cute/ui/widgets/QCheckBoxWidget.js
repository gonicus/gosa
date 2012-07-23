qx.Class.define("cute.ui.widgets.QCheckBoxWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    this._chkBoxWidget = new qx.ui.form.CheckBox();
    this.add(this._chkBoxWidget);
    this.bind("label", this._chkBoxWidget, "label");
    this._chkBoxWidget.addListener("changeValue", function(){
        this.getValue().removeAll();
        this.getValue().push(this._chkBoxWidget.getValue());
        this.fireDataEvent("valueChanged", this.getValue());
      }, this);
  },

  properties: {

    /* Tells the widget how to display its contents
     * e.g. for mode 'password' show [***   ] only.
     * */
    label : {
      init : "",
      check : "String",
      event : "_labelChanged"
    }
  },

  members: {

    _chkBoxWidget: null,

    /* Apply method for the value property.
     * This method will regenerate the gui.
     * */
    _applyValue: function(value, old_value){
      if(value && value.length){
        this._chkBoxWidget.setValue(value.getItem(0));
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
