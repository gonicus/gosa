/*
#asset(qx/icon/${qx.icontheme}/48/status/dialog-information.png)
*/

qx.Class.define("cute.io.WebSocket", {
  extend : qx.core.Object,
  type   : "singleton",

  construct: function(){
    this.base(arguments);
    this.__ws = null;
  },

  members : {

    reconnect : function() {
      var loc = window.location;
      var protocol = "";

      if (this.__ws) {
        this.__ws.close();
      }

      if (qx.core.Environment.get("io.ssl")) {
        protocol = "wss";
      } else {
        protocol = "ws";
      }

      var ws_uri = protocol + "://" + loc.host + cute.Config.ws;

      if ("WebSocket" in window) {
         this.__ws = new WebSocket(ws_uri);
      } else {
         // Firefox 7/8 currently prefixes the WebSocket object
         this.__ws = new MozWebSocket(ws_uri);
      }

      this.__ws.onmessage = function(e) {
        var timeout = 5000;
        var message = e['data'];

        // Create bubble with timeout
        var popup = new qx.ui.basic.Atom(message, "icon/48/status/dialog-information.png").set({
            backgroundColor : "#0A0A0A",
            textColor : "#F0F0F0",
            decorator : "scroll-knob",
            iconPosition : "left",
            padding : 5,
            paddingRight : 20,
            zIndex : 10000,
            opacity : 0.8,
            allowGrowY: false
        });
        var doc = qx.core.Init.getApplication().getRoot();
        doc.add(popup, {right: 15, bottom: 15});

        var timer = qx.util.TimerManager.getInstance();
        timer.start(function(userData, timerId){
          popup.destroy();
        }, 0, this, null, timeout);
      }
    }
  }

});
