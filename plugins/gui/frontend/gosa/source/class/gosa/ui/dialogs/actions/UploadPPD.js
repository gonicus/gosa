/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/*
#asset(gosa/*)
*/
qx.Class.define("gosa.ui.dialogs.actions.UploadPPD", {

  extend: gosa.ui.dialogs.actions.Base,

  construct: function(actionController) {
    this.base(arguments, actionController, this.tr("Upload PPD file"));
    this.__initWidgets();
  },

  statics : {
    RPC_CALLS : ["uploadPPD"]
  },

  properties : {

    appearance : {
      init : "gosa-dialog-uploadppd",
      refine : true
    }
  },

  members : {

    __uploadMgr : null,

    __initWidgets : function() {
      this._createChildControl("infomessage");
      this.__uploadMgr = new com.zenesis.qx.upload.UploadMgr(this.getChildControl("upload-button"));
      this.__uploadMgr.addListener("addFile", this.__onFileAdded, this);
      this._createChildControl("cancel-button");
    },

    __onFileAdded : function(ev) {
      var fileReader = new qx.bom.FileReader();
      fileReader.addListener("load", this.__onFileLoad, this);
      fileReader.readAsText(ev.getData().getBrowserObject());
    },

    __onFileLoad : function(ev) {
      this._actionController.callMethod("uploadPPD", ev.getData().content)
        .bind(this)
        .then(function(result) {

          // Wait until the backend notifies about the new printer models.
          var sseListener = gosa.io.Sse.getInstance().addListener("ObjectPropertyValuesChanged", function(ev) {
            var data = ev.getData();

            if (data.UUID === null) {
              var entry = data.Change.find(function(item) {
                return item.PropertyName === "serverPPD";
              });

              if (entry) {
                var models = JSON.parse(entry.NewValues);
                if (models.hasOwnProperty(result.file_name)) {
                  // Select printer model in widget.
                  gosa.io.Sse.getInstance().removeListenerById(sseListener);
                  var modelWidget = this.__findWidget("serverPPD");
                  modelWidget.setWidgetValue(0, result.file_name);
                  this.destroy();
                }
              }
            }
          }, this);

          // Select manufacturer in widget. This also invokes the sse event for the new models.
          var makerWidget = this.__findWidget("maker");
          makerWidget.setWidgetValue(0, result.manufacturer);
        });
    },

    /**
     * Searches for the widget for a given attribute name.
     *
     * @param name {String}
     * @return {gosa.ui.widgets.Widget | null}
     */
    __findWidget : function(name) {
      if (qx.core.Environment.get("qx.debug")) {
        qx.core.Assert.assertString(name);
      }

      var contexts = this._actionController.getWidget().getContexts();
      var widgetRegistry;

      for (var i = 0; i < contexts.length; i++) {
        widgetRegistry = contexts[i].getWidgetRegistry().getMap();
        if (widgetRegistry[name]) {
          return widgetRegistry[name];
        }
      }
      return null;
    },

    // overridden
    _createChildControlImpl : function(id, hash) {
      var control;

      switch (id) {
        case "infomessage":
          control = new qx.ui.basic.Label(this.tr("PPD files describe the features and capabilities of a PostScript printer. Please select the appropriate file distributed by the vendor of your printer."));
          control.set({
            rich : true,
            wrap : true
          });
          this.addElement(control);
          break;

        case "upload-button":
          control = gosa.ui.base.Buttons.getButton(qx.locale.Manager.tr("Select file..."), "@Ligature/folder");
          this.addElement(control);
          break;

        case "cancel-button":
          control = gosa.ui.base.Buttons.getCancelButton();
          control.addListener("execute", this.destroy, this);
          this.addElement(control);
          break;
      }

      return control || this.base(arguments, id, hash);
    }
  },

  destruct : function() {
    this._disposeObjects("__uploadMgr");
  }
});
