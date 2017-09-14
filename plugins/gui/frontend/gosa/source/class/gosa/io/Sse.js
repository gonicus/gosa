/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/*
#asset(gosa/*)
*/

/**
 * SSE: Server-sent events (receives information from the server/backend)
 * */
qx.Class.define("gosa.io.Sse", {

  extend : qx.core.Object,

  type   : "singleton",

  construct: function(){
    this.base(arguments);
    this.__eventSource = null;
  },

  destruct : function(){
    this.__eventSource = null;
  },

  events: {
    "objectRemoved": "qx.event.type.Data",
    "objectCreated": "qx.event.type.Data",
    "objectModified": "qx.event.type.Data",
    "objectClosing": "qx.event.type.Data",
    "objectMoved": "qx.event.type.Data",
    "pluginUpdate": "qx.event.type.Data",
    "workflowUpdate": "qx.event.type.Data",
    "ObjectPropertyValuesChanged": "qx.event.type.Data",
    "ExtensionAllowed": "qx.event.type.Data"
  },

  properties: {
    connected: {
      check: "Boolean",
      init: false,
      event: "changeConnected"
    }
  },

  members : {

    __eventSource: null,

    reconnect : function() {

      if (this.__eventSource) {
        this.__eventSource.close();
      }

      var uri = window.location.protocol +"//" + window.location.host + gosa.Config.sse;

      this.__eventSource = new EventSource(uri);

      this.__eventSource.addEventListener("notification", function (e) {
        var message = qx.lang.Json.parse(e.data);
        this._handleNotificationMessage(message);
      }.bind(this), false);

      this.__eventSource.addEventListener("objectChange", function (e) {
        var message = qx.lang.Json.parse(e.data);
        this._handleObjectChangeMessage(message);
      }.bind(this), false);

      this.__eventSource.addEventListener("objectCloseAnnouncement", function (e) {
        var message = qx.lang.Json.parse(e.data);
        this._handleObjectCloseAnnouncement(message);
      }.bind(this), false);

      this.__eventSource.addEventListener("pluginUpdate", function (e) {
        var message = qx.lang.Json.parse(e.data);
        this.fireDataEvent("pluginUpdate", message['namespace']);
      }.bind(this), false);

      this.__eventSource.addEventListener("workflowUpdate", function (e) {
        var message = qx.lang.Json.parse(e.data);
        this.fireDataEvent("workflowUpdate", message);
      }.bind(this), false);

      this.__eventSource.addEventListener("BackendException", function (e) {
        var message = qx.lang.Json.parse(e.data);
        var title = qx.locale.Manager.tr("%1 backend error", message.BackendName);
        var error = qx.locale.Manager.tr("%1 operation failed", message.Operation)+" "+message.ErrorMessage;
        // create error dialog to inform user
        var dialog = new gosa.ui.dialogs.Error(error, title);
        this.log.error(title+": "+error);
        dialog.open();
      }.bind(this), false);

      ["ObjectPropertyValuesChanged", "ExtensionAllowed"].forEach(function(eventName) {
        this.__eventSource.addEventListener(eventName, function (e) {
          var message = qx.lang.Json.parse(e.data);
          this.fireDataEvent(e.type, message);
        }.bind(this), false);
      }, this);

      this.__eventSource.onerror = function (e) {
        var readyState = e.currentTarget.readyState;
        if (readyState !== EventSource.OPEN) {
          // Connection was closed.
          this.setConnected(false);
        }
      }.bind(this);
      this.__eventSource.onopen = function(e) {
        var readyState = e.currentTarget.readyState;
        if (readyState === EventSource.OPEN) {
          // Connection was opened.
          this.setConnected(true);
        }
      }.bind(this);
    },

    /**
     * Handle object change messages and fire up events
     * to inform other objects of the changes. E.g Lists.
     */
    _handleObjectChangeMessage : function(info) {
      if(info['changeType'] === "update"){
        this.fireDataEvent("objectModified", info);
      } else if(info['changeType'] === "remove") {
        this.fireDataEvent("objectRemoved", info);
      } else if(info['changeType'] === "create") {
        this.fireDataEvent("objectCreated", info);
      } else if(info['changeType'] === "move") {
        this.fireDataEvent("objectMoved", info);
      }else{
        this.error("unhandled sse event: " + info['changeType']);
      }
    },

    _handleNotificationMessage : function(info) {
      var timeout = 5000;
      var icon = gosa.Config.getImagePath("status/dialog-information.png", 48);
      var title = "";
      if (info['timeout']) {
        timeout = info['timeout'];
      }
      if (info['icon']) {
        if (info['icon'] === "_no_icon_") {
          icon = gosa.Config.getImagePath("status/dialog-information.png", 48);
        } else if (info['icon'].substring(0, 7) === "base64:") {
          icon = "data:image/png;base64, " + info['icon'].substring(7);
        } else {
          icon = gosa.Config.getImagePath("status/" + info['icon'] + ".png", 48);
        }
      }
      if (info['title']) {
        title = '<div style="text-align: center;"><b>' + info['title'] + '</b></div>';
      }

      if (gosa.Config.notifications && gosa.Config.notifications.checkPermission() === 0) {
        var data = qx.util.Base64.encode("<div style='padding:5px'><img src='" + icon + "' align='left'><span style='font-family: arial, verdana, sans-serif;'>" + title + info['body'] + "</span></div>");
        var notification = gosa.Config.notifications.createHTMLNotification("data:text/html;charset=utf-8;base64," + data);
        notification.show();
        qx.event.Timer.once(function() {
          notification.cancel();
        }, this, timeout);

      } else {

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
        popup.addListener("click", function(){ this.closePopup(popup); }, this);
        this.showPopup(popup);

        qx.event.Timer.once(function() {
          this.closePopup(popup);
        }, this, timeout);

      }
    },

    _handleObjectCloseAnnouncement : function(info) {
      this.fireDataEvent("objectClosing", info);
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

      qx.bom.element.Animation.animate(popup.getContentElement().getDomElement(), desc);
      setTimeout(function() {if (popup){ popup.destroy();}}, duration + 100);
    },

    showPopup : function(popup) {
      //TODO: take care about multiple popups at one time (positioning)
      var doc = qx.core.Init.getApplication().getRoot();
      doc.add(popup, {right: 15, bottom: 15});
    }
  }
});
