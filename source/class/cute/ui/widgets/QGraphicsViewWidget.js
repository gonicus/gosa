qx.Class.define("cute.ui.widgets.QGraphicsViewWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    this._widget = new qx.ui.basic.Image("http://www.google.de/images/srpr/logo3w.png");
    this.add(this._widget);
  },

  properties: {

  },

  members: {

    _widget: null,

    /* Apply method for the value property.
     * This method will regenerate the gui.
     * */
    _applyValue: function(value, old_value){

      if(value && value.length){
        //this._widget.setSource(value.getItem(0));
        this._initialized = true;
      }
    },

    setInvalidMessage: function(message){
      //this._widget.setInvalidMessage(message);
    },

    resetInvalidMessage: function(){
      //this._widget.resetInvalidMessage();
    },

    focus: function(){
      //this._widget.focus();
    },

    setValid: function(bool){
      //this._widget.setValid(bool);
    }
  }
});
