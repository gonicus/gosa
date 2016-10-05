/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.Tools", {

  type: "static",

  statics: {

    createActionUrl: function(action, target){
      var url = document.location.origin + document.location.pathname;
      url += "#" + action + gosa.Config.actionDelimiter + target;
      return(url);
    },

    getLocale: function(){
      var locale;
      if (gosa.Config.locale) {
        locale = gosa.Config.locale;
      } else {
        locale = qx.bom.client.Locale.getLocale();
        var variant = qx.bom.client.Locale.getVariant();
        if (locale && variant) {
          locale = locale + "-" + variant;
        }
      }
      return(locale);
    },

    serialize : function(queue)
    {
      var timer = qx.util.TimerManager.getInstance();
      var locked = false;

      timer.start(function(userData, timerId){
        if (locked) {
          return;
        }

        locked = true;

        var entry = queue.shift();
        if (entry === undefined) {
          timer.stop();
          return;
        }

        var func = entry[0];
        var context = entry[1];
        var params = entry[2];
        params.push(function() {
          locked = false;
        });
        func.apply(context, params);
      }, 10, null, null, 0);
    },

    /**
     * Get an error string to the given error code
     *
     * @see https://developers.yubico.com/U2F/Libraries/Client_error_codes.html
     * @param code {Number} error code
     * @private
     */
    getU2FErrorMessage: function(code) {
      switch(code) {
        case 1:
          return qx.locale.Manager.tr("Unkown error");
        case 2:
          return qx.locale.Manager.tr("Bad request");
        case 3:
          return qx.locale.Manager.tr("Client configuration is not supported");
        case 4:
          return qx.locale.Manager.tr("The presented device is not eligible for this request");
        case 5:
          return qx.locale.Manager.tr("Timeout reached before request could be satisfied");
      }
    }
  }
});
