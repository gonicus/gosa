/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * @lint ignoreUndefined(com)
 * */
qx.Class.define("gosa.ui.widgets.QGraphicsViewWidget", {

  extend: gosa.ui.widgets.Widget,


  construct: function(){
    this.base(arguments);
    this.contents.setLayout(new qx.ui.layout.VBox(5));
    this.setDecorator("main");

    this._defaultImage = gosa.Config.getImagePath("unset-user-image.png", 128);

    this._widget = new qx.ui.basic.Image(this._defaultImage);
    this._widget.addListener("loadingFailed", function(){
        this._widget.setSource(this._defaultImage);
        this.error("*** Invalid Image given! ***");
      }, this);

    var container = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
    container.add(this._widget, {top:1, bottom:1, left:1, right:1});
    this.contents.add(container);

    // Pre-create a video capture area
    this.__cap = new capture.Capture().set({
        width: 320,
        height: 240
    });

    this.__cap_win = new qx.ui.window.Window(this.tr("Image capture"));
    this.__cap_win.setShowMaximize(false);
    this.__cap_win.setShowMinimize(false);
    this.__cap_win.setAlwaysOnTop(true);
    this.__cap_win.setResizable(false);
    this.__cap_win.setLayout(new qx.ui.layout.VBox(10));
    this.__cap_win.add(this.__cap);
    this.__cap_win.addListener("beforeClose", function() {
        this.__cap.stop();
    }, this);

    // Add capture button
    var paneLayout = new qx.ui.layout.HBox().set({
      spacing: 4,
      alignX : "center"
    });
    var buttonPane = new qx.ui.container.Composite(paneLayout);
    var cap_button = new qx.ui.form.Button(null, "@Ligature/camera/22");
    cap_button.setWidth(64);
    cap_button.addListener('execute', function() {
        var data = this.__cap.getImageData('jpeg').split(/,(.+)?/)[1];
        this.setValue(new qx.data.Array([new gosa.io.types.Binary(data)]));
        this.fireDataEvent("changeValue", this.getValue());
        this.__cap.stop();
        this.__cap_win.hide();
    }, this);

    buttonPane.add(cap_button);
    this.__cap_win.add(buttonPane);

    // Create context menu buttons
    this._changePicture = new qx.ui.menu.Button(this.tr("Upload new image"), "@Ligature/folder/22");
    this._capturePicture = new qx.ui.menu.Button(this.tr("Capture"), "@Ligature/camera/22");
    this._capturePicture.setEnabled(this.__cap.isSupported());
    this._removePicture = new qx.ui.menu.Button(this.tr("Remove image"), "@Ligature/remove/22");
    this._removePicture.setEnabled(false);

    // Establish image upload handling
    var uploader = new com.zenesis.qx.upload.UploadMgr(this._changePicture);
    uploader.setAutoUpload(false);
    uploader.addListener("addFile", function(evt) {
        var file = evt.getData();
        var f = file.getBrowserObject();
        var fr = new qx.bom.FileReader();
        this._widget.setSource(null);
        fr.addListener("load", function(e){
          var data = e.getData().content;
          data = data.replace(/^data:.*;base64,/, "");
          this.setValue(new qx.data.Array([new gosa.io.types.Binary(data)]));
          this.fireDataEvent("changeValue", this.getValue());
        }, this);
        fr.readAsDataURL(f);
      }, this);

    // Create remove image handler
    this._removePicture.addListener("click", function(){
        this.setValue(new qx.data.Array());
        this.fireDataEvent("changeValue", this.getValue());
      }, this);

    // Create capture image handler
    this._capturePicture.addListener("click", function(){
        //this.setValue(new qx.data.Array());
        //this.fireDataEvent("changeValue", this.getValue());

        // Open Capture window and start capturing
        this.__cap_win.show();
        this.__cap_win.center();
        this.__cap.start();
        this.__cap.setCaptureSizeX(200);
        this.__cap.setCaptureSizeY(200);
      }, this);

    // Create context menu
    var menu = new qx.ui.menu.Menu();
    menu.add(this._changePicture);
    menu.add(this._capturePicture);
    menu.add(this._removePicture);
    container.setContextMenu(menu);
    container.addListener('click', function(e){
      menu.open();
      menu.placeToPointer(e);
    }, this);
  },

  properties: {

  },

  destruct : function(){

    // Remove all listeners and then set our values to null.
    qx.event.Registration.removeAllListeners(this.__cap_win);
    qx.event.Registration.removeAllListeners(this._removePicture);
    qx.event.Registration.removeAllListeners(this._capturePicture);
    qx.event.Registration.removeAllListeners(this);

    this.setBuddyOf(null);
    this.setGuiProperties(null);
    this.setValues(null);
    this.setBlockedBy(null);
    this.setValue(null);
    this._defaultImage = null;

    this._disposeObjects("_changePicture", "_removePicture", "_widget", "_capturePicture");
  },

  statics: {
    /* Create a readonly representation of this widget for the given value.
     * This is used while merging object properties.
     * */
    getMergeWidget: function(value){
      var w = new qx.ui.basic.Image();
      if(value.getLength()){
        var source = "data:image/jpeg;base64," + value.getItem(0).get();
        w.setSource(source);
      }
      return(w);
    }
  },

  members: {
    __cap: null,
    __cap_win: null,
    __capturePicture: null,
    _changePicture: null,
    _removePicture: null,
    _widget: null,
    _defaultImage: null,

    /* Returns the widget values in a clean way,
     * to avoid saving null or empty values for an object
     * property.
     * */
    getCleanValues: function()
    {
      return(new qx.data.Array(this.getValue().toArray()));
    },

    /* Apply method for the value property.
     * */
    _applyValue: function(value, old_value){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(value === null){
        return;
      }

      if (this._widget){
        this._removePicture.setEnabled(false);
        if (value && value.length && value.getItem(0)){
            var source = "data:image/jpeg;base64," + value.getItem(0).get();
            this._widget.setSource(source);
            this._removePicture.setEnabled(true);
        } else{
          this._widget.setSource(this._defaultImage);
        }
      }
    },

    focus: function(){
      this._widget.focus();
    }
  }
});
