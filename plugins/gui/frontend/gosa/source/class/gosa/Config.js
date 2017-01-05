/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.Config", {

  type: "static",

  statics: {

    url: "/rpc",
    sse: "/events",
    spath: "/static",
    service: "GOsa JSON-RPC service",
    actionDelimiter: '#',
    timeout: 60000,
    notifications: window.webkitNotifications || window.notifications,

    AUTH_OTP_REQUIRED: 2,
    AUTH_U2F_REQUIRED: 3,
    AUTH_FAILED: 99,
    AUTH_SUCCESS: 100,

    getTheme : function()
    {
      if (gosa.Config.theme) {
          return gosa.Config.theme;
      }

      return "default";
    },

    getImagePath : function(icon, size)
    {
        if (!size) {
            size = "22";
        }

        return "gosa/images/" + size + "/" + icon;
    },

    getLocale : function() {
      if (!gosa.Config.locale) {
        gosa.Config.locale = qx.bom.client.Locale.getLocale();
        var variant = qx.bom.client.Locale.getVariant();
        if (gosa.Config.locale && variant) {
          gosa.Config.locale = gosa.Config.locale + "-" + variant;
        }
      }
      return gosa.Config.locale;
    }
  }
});
