qx.Class.define("cute.ui.widgets.QGraphicsViewWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    this._widget = new qx.ui.basic.Image("cute/noPicture.jpeg");
    this.add(this._widget);

    var upload = new cute.ui.widgets.Upload();
    upload.addListener("selected",  function(e) {
        var fr = new qx.bom.FileReader();
        fr.addListener("load", function(e){
            var data = e.getData()['content'];
            this.setValue(new qx.data.Array([new cute.proxy.dataTypes.Binary(qx.util.Base64.encode(data))]));
          }, this);
        fr.readAsBinaryString(upload.getFile());
      }, this);
    this.add(upload);

    this._widget.addListener("click", function(){
        upload.click();
      }, this);
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
