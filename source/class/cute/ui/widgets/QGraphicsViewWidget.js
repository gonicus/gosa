qx.Class.define("cute.ui.widgets.QGraphicsViewWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    var theme = "default";
    if (cute.Config.theme) {
      theme = cute.Config.theme;
    }

    this._widget = new qx.ui.basic.Image("cute/themes/" + theme + "/noPicture.jpeg");
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
          this.setValue(new qx.data.Array([new cute.io.types.Binary(data)]));
          this.fireDataEvent("valueChanged", this.getValue());
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
        this._widget.setSource(source);
      }
    },

    focus: function(){
      this._widget.focus();
    }
  }
});
