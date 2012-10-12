qx.Class.define("gosa.Config", {

  type: "static",

  statics: {

    url: "/rpc",
    ws: "/ws",
    spath: "/static",
    service: "Clacks JSON-RPC service",
    actionDelimiter: '#',
    timeout: 60000,
    notifications: window.webkitNotifications || window.notifications,

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

        return "gosa/themes/" + gosa.Config.getTheme() + "/" + size + "/" + icon;
    }
  }
});
