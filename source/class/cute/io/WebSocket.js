/*
#asset(qx/icon/${qx.icontheme}/48/status/*)
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

      var that = this;
      this.__ws.onmessage = function(e) {
        var message = qx.lang.Json.parse(e['data']);

        // Check if we can handle that message
        var capmessage = message[0].charAt(0).toUpperCase() + message[0].slice(1)
        var method = "_handle" + capmessage + "Message";
        if (that[method]) {
          that[method](message[1]);
        } else {
          that.error("*** no idea how to handle '" + message[0] + "' messages");
        }
      }
    },

    _handleNotificationMessage : function(info) {
      var timeout = 5000;
      var icon = "icon/48/status/dialog-information.png"
      var title = "";
      if (info['timeout']) {
        timeout = info['timeout'];
      }
      if (info['icon']) {
        if (info['icon'] == "_no_icon_") {
          icon = "icon/48/status/dialog-information.png"
        } else if (info['icon'].substring(0, 7) == "base64:") {
          icon = "data:image/png;base64, " + info['icon'].substring(7);
        } else {
          icon = "icon/48/status/" + info['icon'] + ".png";
        }
      }
      if (info['title']) {
        title = "<center><b>" + info['title'] + "</b></center>";
      }

      // Create bubble with timeout
      var popup = new qx.ui.basic.Atom(title + info["body"].replace(/\n/g, '<br />'), icon).set({
          backgroundColor : "#0A0A0A",
          textColor : "#F0F0F0",
          decorator : "scroll-knob",
          iconPosition : "left",
          padding : 8,
          paddingRight : 20,
          zIndex : 10000,
          opacity : 0.8,
          rich : true
      });
      popup.addListener("click", function(e){ this.closePopup(popup); }, this);
      this.showPopup(popup)

      var timer = qx.util.TimerManager.getInstance();
      timer.start(function(userData, timerId){
        this.closePopup(popup);
      }, 0, this, null, timeout);
    },

    closePopup : function(popup) {
      //TODO: take care about multiple popups at one time (rearranging)

      if (!popup) {
        return;
      }

      var duration = 250;
      var desc = {duration: duration, keep: 100, timing: "ease-out", keyFrames : {
        0 : {"opacity" : 0.8},
        100 : {"opacity": 0, display: "none"}
      }};

      qx.bom.element.Animation.animate(popup.getContainerElement().getDomElement(), desc);
      setTimeout(function() {if (popup){ popup.destroy();}}, duration + 100);
    },

    showPopup : function(popup) {
      //TODO: take care about multiple popups at one time (positioning)
      var doc = qx.core.Init.getApplication().getRoot();
      doc.add(popup, {right: 15, bottom: 15});
    },

    wordwrap : function(str, width, brk, cut) {
      brk = brk || '\n';
      width = width || 75;
      cut = cut || false;

      if (!str) { return str; }

      var regex = '.{1,' +width+ '}(\\s|$)' + (cut ? '|.{' +width+ '}|.+$' : '|\\S+?(\\s|$)');

      return str.match( RegExp(regex, 'g') ).join( brk );
    }
  }

});
