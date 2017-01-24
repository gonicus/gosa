/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.util.DragDropHelper", {
  extend: qx.core.Object,
  type : "singleton",

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "loaded": "qx.event.type.Data"
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    /**
     * Handles HTML5 drop events (dropping external files on dom element)
     * @param e {Event}
     * @param type {String} type of upload file e.g. workflows or widgets
     */
    onHtml5Drop : function(e, type) {
      var filereader;
      for (var i=0, l = e.dataTransfer.files.length; i<l; i++) {
        var file = e.dataTransfer.files[i];
        if (file.type === "application/javascript") {
          filereader = new FileReader();
          filereader.onload = qx.lang.Function.curry(this._onJsFileLoaded, file, type||"widgets").bind(this);
          filereader.readAsBinaryString(file);
        } else if (file.type === "application/zip") {
          filereader = new FileReader();
          filereader.onload = qx.lang.Function.curry(this._onZipFileLoaded, file, type||"widgets").bind(this);
          filereader.readAsBinaryString(file);
        } else {
          this.error("Unhandled file type "+file.type+" for file "+file.name+". Skipping upload!");
        }
      }

      e.stopPropagation();
      e.preventDefault();
    },

    /**
     * Handle 'onload' events from {FileReader} for javascript files
     * @param file {File}
     * @param type {String} type of uploaded file (e.g. workflow, widgets)
     * @param ev {ProgressEvent}
     */
    _onJsFileLoaded: function(file, type, ev) {
      var packageName = file.name.substring(0, file.name.length-3);
      qx.core.Environment.add(packageName+".source", "external");
      qx.lang.Function.globalEval(ev.target.result);
      this.fireDataEvent("loaded", packageName);
    },

    /**
     * Handle 'onload' events from {FileReader} for zip files
     * @param file {File}
     * @param type {String} type of uploaded file (e.g. workflow, widgets)
     */
    _onZipFileLoaded: function(file, type) {
      // register temporary upload path
      gosa.io.Rpc.getInstance().cA("registerUploadPath", type)
      .then(function(result) {
        var path = result[1];
        var uploadMgr = new gosa.util.UploadMgr(null, path);
        uploadMgr.uploadFile(file);
      }, this)
    }
  }
});
