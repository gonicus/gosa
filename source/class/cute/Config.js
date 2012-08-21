qx.Class.define("cute.Config", {

  type: "static",

  statics: {
    url: "/rpc",
    ws: "/ws",
    service: "Clacks JSON-RPC service",
    timeout: 60000,
    notifications: window.webkitNotifications || window.notifications,

    getTheme : function()
    {
      if (cute.Config.theme) {
          return cute.Config.theme;
      }

      return "default";
    },

    getImagePath : function(icon, size)
    {
        if (!size) {
            size = "22";
        }

        return "cute/themes/" + cute.Config.getTheme() + "/" + size + "/" + icon;
    }
  }
});
