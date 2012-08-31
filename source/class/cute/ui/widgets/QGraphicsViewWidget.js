

/**
 * @lint ignoreUndefined(com)
 * */
qx.Class.define("cute.ui.widgets.QGraphicsViewWidget", {

  extend: cute.ui.widgets.Widget,

  
  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));
    this.setDecorator("main");

    this._defaultImage = cute.Config.getImagePath("unset-user-image.png", 128);

    this._widget = new qx.ui.basic.Image(this._defaultImage);
    this._widget.addListener("loadingFailed", function(){
        this._widget.setSource(this._defaultImage);
        this.error("*** Invalid Image given! ***");
      }, this);

    var container = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
    container.add(this._widget, {top:1, bottom:1, left:1, right:1});
    this.add(container);
    
    // Create context menu buttons
    this._changePicture = new qx.ui.menu.Button(this.tr("Change image"));
    this._removePicture = new qx.ui.menu.Button(this.tr("Remove image"));
    this._removePicture.setEnabled(false);

    // Establish image upload handling
    var uploader = new com.zenesis.qx.upload.UploadMgr(this._changePicture);
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
          this.fireDataEvent("changeValue", this.getValue());
        }, this);
        fr.readAsDataURL(f);
      }, this);

    // Create remove image handler
    this._removePicture.addListener("click", function(){
        this.setValue(new qx.data.Array());
        this.fireDataEvent("changeValue", this.getValue());
      }, this);

    // Create context menu
    var menu = new qx.ui.menu.Menu();
    menu.add(this._changePicture);
    menu.add(this._removePicture);
    container.setContextMenu(menu);
    container.addListener('click', function(e){
      menu.open();
      menu.placeToMouse(e);
    }, this);
  },

  properties: {

  },

  destruct : function(){
    this._defaultImage = null;
    this._disposeObjects("_changePicture", "_removePicture", "_widget");
  },

  members: {
    _changePicture: null,
    _removePicture: null,
    _widget: null,
    _defaultImage: null,

    /* Apply method for the value property.
     * */
    _applyValue: function(value, old_value){
      if(this._widget){
        this._removePicture.setEnabled(false);
        if(value && value.length && value.getItem(0)){
          var source = "data:image/jpeg;base64," + value.getItem(0).get();
          this._widget.setSource(source);
          this._removePicture.setEnabled(true);
        }else{
          this._widget.setSource(this._defaultImage);
        }
      }
    },

    focus: function(){
      this._widget.focus();
    }
  }
});
