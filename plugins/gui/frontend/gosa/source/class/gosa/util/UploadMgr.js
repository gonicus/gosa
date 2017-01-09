/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Extend {com.zenesis.qx.upload.UploadMgr} to allow files to e uploaded via HTML5 drop
*/
qx.Class.define("gosa.util.UploadMgr", {
  extend : com.zenesis.qx.upload.UploadMgr,
    
  members : {
    __lastId : 0,

    /**
     * Allocates a unique ID
     *
     * @returns {Number}
     */
    _getUniqueFileId: function() {
      return ++this.__lastId;
    },

    /**
     * Upload file directly to the backend
     *
     * @param bomFile {File}
     */
    uploadFile: function(bomFile) {
      var id = "upload-" + this._getUniqueFileId();
      var filename = typeof bomFile.name != "undefined" ? bomFile.name : bomFile.fileName;
      var file = new com.zenesis.qx.upload.File(bomFile, filename, id);
      var fileSize = typeof bomFile.size != "undefined" ? bomFile.size : bomFile.fileSize;
      file.setSize(fileSize);
      file.setUploadWidget(new com.zenesis.qx.upload.UploadButton());

      this.getUploadHandler()._addFile(file);
      if (this.getAutoUpload())
        this.getUploadHandler().beginUploads();
    }
  }
});