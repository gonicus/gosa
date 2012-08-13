qx.Class.define("cute.Config", {

  type: "static",

  statics: {
    url: "/rpc",
    ws: "/ws",
    service: "Clacks JSON-RPC service",
    timeout: 60000,
    notifications: window.webkitNotifications || window.notifications
  }
});
