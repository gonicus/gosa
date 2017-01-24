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
 * "upload-dropbox" childcontrol
*/
qx.Mixin.define("gosa.upload.MDragUpload", {

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    if (this.getBounds()) {
      this._applyDragListeners();
    } else {
      this.addListenerOnce("appear", function() {
        this._applyDragListeners();
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
      apply: "_applyUploadMode"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __hasEmptyInfo: null,

    /**
     * Apply dragover/-leave listeners to the dashboard to recognize File uploads via Drag&Drop
     */
    _applyDragListeners: function() {
      var element = this.getContentElement().getDomElement();
      element.ondragexit = function() {
        this.setUploadMode(false);
      }.bind(this);

      element.ondragenter = function(ev) {
        if (ev.dataTransfer && ev.dataTransfer.items.length > 0) {
          // we have something to drop
          this.setUploadMode(true);
          ev.dataTransfer.effectAllowed = "none";
          ev.preventDefault();
        }
      }.bind(this);

      element.ondragover = function(ev) {
        ev.preventDefault();
      };

      element.ondragend = function() {
        this.setUploadMode(false);
      }.bind(this);

      element.ondrop = function(ev) {
        ev.preventDefault();
      };
    },

    // property apply
    _applyUploadMode: function(value) {
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
    }
  }
});