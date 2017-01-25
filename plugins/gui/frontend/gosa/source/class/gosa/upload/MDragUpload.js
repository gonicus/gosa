/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Add upload via drag&drop feature to this widget. The including widget must have a
 * "upload-dropbox" childcontrol.
 * Including classes must also include the {gosa.util.MMethodChaining} mixin.
*/
qx.Mixin.define("gosa.upload.MDragUpload", {

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.addHook("after", "_createChildControlImpl", this._createMDragUploadChildControlImpl, this);
    if (this.getBounds()) {
      this._applyStartDragListeners();
    } else {
      this.addListenerOnce("appear", function() {
        this._applyStartDragListeners();
      }, this);
    }
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    uploadMode: {
      check: "Boolean",
      init: false,
      apply: "__applyUploadMode"
    },

    uploadType: {
      check: ["widget", "workflow"],
      init: "widget"
    },

    uploadHint: {
      check: "String",
      init: ""
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __hasEmptyInfo: null,

    // overridden
    _createMDragUploadChildControlImpl: function(id) {
      var control;

      switch(id) {
        case "upload-overlay":
          control = new qx.ui.container.Composite();
          control.setZIndex(1000000);
          control.exclude();
          qx.core.Init.getApplication().getRoot().add(control, {edge: 0});
          this.getChildControl("upload-dropbox").bind("visibility", control, "visibility");
          break;

        case "upload-dropbox":
          control = new qx.ui.container.Composite(new qx.ui.layout.Atom().set({center: true}));
          var dropBox = new qx.ui.basic.Atom(this.getUploadHint(), "@Ligature/upload/128");
          dropBox.set({
            allowGrowY: false
          });
          control.setAnonymous(true);
          control.add(dropBox);
          control.exclude();
          qx.core.Init.getApplication().getRoot().add(control, {edge: 0});
          break;
      }
      return control;
    },

    __onStopDragging: function(ev) {
      ev.preventDefault();
      this.setUploadMode(false);
    },

    /**
     * Apply dragover/-leave listeners to the dashboard to recognize File uploads via Drag&Drop
     */
    _applyStartDragListeners: function() {
      // add the start listener to this widget
      this.getContentElement().getDomElement().addEventListener("dragenter", function(ev) {
        console.log("dragenter " + ev.currentTarget.getAttribute("qxclass"));
        // ev.preventDefault();
        if (ev.dataTransfer && ev.dataTransfer.items.length > 0) {
          // we have something to drop
          this.setUploadMode(true);
        }
      }.bind(this), false);
      if (this.getChildControl("upload-overlay").getBounds()) {
        this._applyDragListeners();
      } else {
        this.getChildControl("upload-overlay").addListenerOnce("appear", function() {
          this._applyDragListeners();
        }, this);
      }

    },

      /**
     * Apply dragover/-leave listeners to the dashboard to recognize File uploads via Drag&Drop
     */
    _applyDragListeners: function() {
      var element = this.getChildControl("upload-overlay").getContentElement().getDomElement();
      console.log("applying listeners to "+element.getAttribute("qxclass"));
      element.addEventListener("dragexit", function(ev) {
        console.log("dragexit "+ev.currentTarget.getAttribute("qxclass"));
        this.setUploadMode(false);
      }.bind(this), false);

      element.addEventListener("dragover", function(ev) {
        ev.preventDefault();
        this.setUploadMode(true);
        ev.dataTransfer.dropEffect = 'move';
        console.log("dragover "+ev.currentTarget.getAttribute("qxclass"));
      }.bind(this), false);
      document.addEventListener("dragleave", function(ev) {
        // ev.preventDefault();
        console.log("dragleave");
        this.__onStopDragging(ev);
      }.bind(this), false);
      element.addEventListener("dragend", function(ev) {
        console.log("dragend "+ev.currentTarget.getAttribute("qxclass"));
        this.setUploadMode(false);
      }.bind(this), false);

      element.addEventListener("drop", function(ev) {
        gosa.util.DragDropHelper.getInstance().onHtml5Drop.call(gosa.util.DragDropHelper.getInstance(), ev, this.getUploadType());
        this.__onStopDragging(ev);
      }.bind(this), false);
    },

    // property apply
    __applyUploadMode: function(value, old) {
      if (value === true) {
        this.getChildControl("upload-dropbox").show();
        if (this.hasChildControl("empty-info") && this.getChildControl("empty-info").isVisible()) {
          this.getChildControl("empty-info").exclude();
          this.__hasEmptyInfo = true;
        } else {
          this.__hasEmptyInfo = false;
        }
      } else {
        this.getChildControl("upload-dropbox").exclude();
        if (this.__hasEmptyInfo === true) {
          this.getChildControl("empty-info").show();
        }
      }
      if (this._applyUploadMode) {
        this._applyUploadMode(value, old);
      }
    }
  }
});