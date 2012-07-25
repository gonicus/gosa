qx.Class.define("cute.ui.widgets.QGraphicsViewWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    this._widget = new qx.ui.basic.Image("cute/noPicture.jpeg");
    this.add(this._widget);

    var btn = new com.zenesis.qx.upload.UploadButton("Add File");
    var uploader = new com.zenesis.qx.upload.UploadMgr(btn);
    uploader.setAutoUpload(false);

    this.add(btn);
    uploader.addListener("addFile", function(evt) {
        var file = evt.getData();
        var f = file.getBrowserObject();
        var fr = new qx.bom.FileReader();
        this._widget.setSource("cute/loading.gif");
        fr.addListener("load", function(e){
          var data = e.getData().content;
          data = data.replace(/^data:.*;base64,/, "");
          this.setValue(new qx.data.Array([new cute.proxy.dataTypes.Binary(data)]));
        }, this);
        fr.readAsDataURL(f);
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

        console.log()
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
