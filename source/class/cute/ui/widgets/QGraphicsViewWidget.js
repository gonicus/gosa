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
    this._widget.addListener("loadingFailed", function(){
        this._widget.setSource("cute/themes/" + theme + "/noPicture.jpeg");
        this.error("*** Invalid Image given! ***")
      }, this);

    var container = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
    container.setBackgroundColor("#DDDDDD");
    container.add(this._widget, {top:0, bottom:0, left:0, right:0});
    this.add(container);

    var uploader = new com.zenesis.qx.upload.UploadMgr(container);
    uploader.setAutoUpload(false);
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
     * */
    _applyValue: function(value, old_value){
      if(value && value.length){
        if(value.getItem(0)){
          var source = "data:image/jpeg;base64," + value.getItem(0).get();
          this._widget.setSource(source);
        }
      }
    },

    focus: function(){
      this._widget.focus();
    }
  }
});
