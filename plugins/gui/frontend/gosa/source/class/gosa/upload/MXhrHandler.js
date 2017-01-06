/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Path {com.zenesis.qx.upload.XhrHandler} to send an XSRF token with every post
*/
qx.Mixin.define("gosa.upload.MXhrHandler", {
  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    // override
    _doUpload: function(file) {
      function sendAsMime(binaryData) {
        body += binaryData + "\r\n";
        body += "--" + boundary + "--";

        xhr.open("POST", action, true);
        setRequestHeader("X-Requested-With", "XMLHttpRequest");
        setRequestHeader("X-File-Name", encodeURIComponent(file.getFilename()));
        setRequestHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
        setRequestHeader("X-XSRFToken", gosa.io.Rpc.getInstance().getXsrfToken());
        xhr.send(body);
      }

      function setRequestHeader(name, value) {
        xhr.setRequestHeader(name, value);
        headerLength += name.length + 2 + value.length + 1;
      }

      /*
       * The upload progress includes the size of the headers, but we cannot ask XMLHttpRequest what the
       * headers were so we count the headers we set and also add these below.  This is never going to be
       * completely accurate, but it gets us a lot closer.
       */
      var headerLength = 0;
      var DEFAULT_HEADERS = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en,en-US;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Length": "" + file.getSize(),
        "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundaryTfptZDRmE8C3dZmW",
        "Host": document.location.host,
        "Pragma": "no-cache",
        "Referer": document.location.href,
        "User-Agent": navigator.userAgent
      };
      if (document.location.origin)
        DEFAULT_HEADERS.Origin = document.location.origin;
      for (var key in DEFAULT_HEADERS)
        headerLength += DEFAULT_HEADERS[key].length + 1;

      var xhr = new XMLHttpRequest();
      if (com.zenesis.qx.upload.XhrHandler.isWithCredentials())
        xhr.withCredentials = true;

      var self = this;

      file.setUserData("com.zenesis.qx.upload.XhrHandler", xhr);

      xhr.upload.onprogress = function(e) {
        self.debug("onprogress: lengthComputable=" + e.lengthComputable + ", total=" + e.total + ", loaded=" + e.loaded + ", headerLength=" + headerLength);
        if (e.lengthComputable) {
          file.setSize(e.total - headerLength);
          file.setProgress(e.loaded - headerLength);
        }
      };

      xhr.onreadystatechange = function() {
        if (xhr.readyState == 4) {
          var response = xhr.responseText;
          // self.debug("xhr server status=" + xhr.status + ", responseText=" +
          // response);
          file.setUserData("com.zenesis.qx.upload.XhrHandler", null);
          self._onCompleted(file, response);
        }
      };

      if (typeof FormData == "function" || typeof FormData == "object") {
        var fd = new FormData();

        // build query string
        var action = this._getUploader().getUploadUrl();
        var params = this._getMergedParams(file);
        for (var name in params)
          fd.append(name, encodeURIComponent(params[name]));
        fd.append("file", file.getBrowserObject());

        xhr.open("POST", action, true);
        setRequestHeader("X-Requested-With", "XMLHttpRequest");
        setRequestHeader("X-File-Name", encodeURIComponent(file.getFilename()));
        setRequestHeader("X-XSRFToken", gosa.io.Rpc.getInstance().getXsrfToken());
        xhr.send(fd);

      } else {
        var browserFile = file.getBrowserObject();
        var boundary = "--------FormData" + Math.random(), body = "", action = this._getUploader().getUploadUrl(), params = this
        ._getMergedParams(file);
        for ( var name in params) {
          body += "--" + boundary + "\r\n";
          body += "Content-Disposition: form-data; name=\"" + name + "\";\r\n\r\n";
          body += params[name] + "\r\n";
        }
        body += "--" + boundary + "\r\n";
        body += "Content-Disposition: form-data; name=\"file\"; filename=\"" + file.getFilename() + "\"\r\n";
        body += "Content-Type: " + (browserFile.type || "application/octet-stream") + "\r\n\r\n";

        if (typeof browserFile.getAsBinary == "function") {
          sendAsMime(browserFile.getAsBinary());
        } else {
          var reader = new FileReader();
          reader.onload = function(evt) {
            sendAsMime(evt.target.result);
          };
          reader.readAsBinaryString(browserFile);
        }
      }
    }
  }
});