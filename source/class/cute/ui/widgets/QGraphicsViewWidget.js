qx.Class.define("cute.ui.widgets.QGraphicsViewWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    this._widget = new qx.ui.basic.Image("cute/noPicture.jpeg");
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
        this._initialized = true;
        var source = "data:image/png;base64," + value.getItem(0).get();
        this._widget.setSource(source);
      }
    },

    setInvalidMessage: function(message){
      this._widget.setInvalidMessage(message);
    },

    resetInvalidMessage: function(){
      this._widget.resetInvalidMessage();
    },

    focus: function(){
      this._widget.focus();
    },

    setValid: function(bool){
      this._widget.setValid(bool);
    }
  }
});
