/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */
/**
 * This class connects model attributes to their widgets.
 */
qx.Class.define("gosa.data.ModelWidgetConnector", {

  extend : qx.core.Object,

  construct : function(object, widget) {
    this.base(arguments);

    this.__object = object;
    this.__widget = widget;
    this.__boundAttributes = [];
  },

  events : {
    "initialized" : "qx.event.type.Event"
  },

  members : {

    __object : null,
    __widget : null,
    __boundAttributes : null,
    __initialized : false,

    /**
     * Connects all widgets that are initialized to their attributes in the object. Skips those that are already
     * connected.
     */
    connectAll : function() {
      gosa.util.Object.iterate(this.__object.attribute_data, function(attributeName, config) {
        if (qx.lang.Array.contains(this.__boundAttributes, attributeName)) {
          return;
        }

        var widgets = this.__findWidgets(attributeName);
        if (!widgets) {
          return;
        }

        this.connect(attributeName, config, widgets.widget, widgets.buddy);
        this.__boundAttributes.push(attributeName);
      }, this);

      if (!this.__initialized) {
        this.__initialized = true;
        this.fireEvent("initialized");
      }
    },

    connect : function(attributeName, config, widget, buddy) {
      this.__handleProperties(config, widget, buddy);

      if (config.hasOwnProperty("blocked_by")) {
        this.__handleBlockedBy(config.blocked_by, widget, buddy, function() {
          this.__initCompleteWidget(widget);
          this.__initCompleteWidget(buddy);
        }, this);
      }
      else {
        this.__initCompleteWidget(widget);
        this.__initCompleteWidget(buddy);
      }

      widget.setValue(this.__object.get(attributeName));
      widget.addListener("changeValue", function(event) {
        this.__object.set(attributeName, event.getData());
        this.__widget.getController().checkValidity();
      }, this);
    },

    __initCompleteWidget : function(widget) {
      if (widget) {
        new qx.util.DeferredCall(function() {
          if (!widget.isDisposed()) {
            widget.setInitComplete(true);
          }
        }).schedule();
      }
    },

    __handleProperties : function(config, widget, buddy) {
      var setMap = {};

      if (config["mandatory"]) {
        setMap.mandatory = !!config.mandatory;
      }
      if (config["readonly"]) {
        setMap.readOnly = !!config.readonly;
      }
      if (config["multivalue"]) {
        setMap.multivalue = !!config.multivalue;
      }
      if (config["default"]) {
        setMap.defaultValue = config["default"];
      }
      if (config["type"]) {
        setMap.type = config.type;
      }
      if (config["case_sensitive"]) {
        setMap.caseSensitive = config.case_sensitive;
      }
      if (config["unique"]) {
        setMap.unique = config.unique;
      }
      if (config["depends_on"]) {
        setMap.dependsOn = config.depends_on;
      }
      if (config["values"]) {
        setMap.values = config.values;
      }

      // set properties
      if (widget) {
        widget.set(setMap);
      }
      if (buddy) {
        buddy.set(setMap);
      }
    },

    __findWidgets : function(name) {
      var contexts = this.__widget.getContexts();

      for (var i = 0; i < contexts.length; i++) {
        if (contexts[i].getWidgetRegistry().getMap()[name]) {
          return {
            widget : contexts[i].getWidgetRegistry().getMap()[name],
            buddy  : contexts[i].getBuddyRegistry().getMap()[name]
          };
        }
      }
      return null;
    },

    __handleBlockedBy : function(value, widget, buddy, callback, context) {
      if (value.length === 0) {
        if (callback) {
          callback.call(context);
        }
        return;
      }
      var allWidgets = [];

      var listenerCallback = function() {
        var block = allWidgets.some(function(item) {
          var value = item.widget.getValue();
          if (value instanceof qx.data.Array && value.getLength() > 0) {
            value = value.getItem(0);
          }
          return value === item.value;
        });

        if (block) {
          if (buddy) {
            buddy.block();
          }
          if (widget) {
            widget.block();
          }
        }
        else {
          if (buddy) {
            buddy.unblock();
          }
          if (widget) {
            widget.unblock();
          }
        }

        if (callback) {
          callback.call(context);
        }
      };

      value.forEach(function(item) {
        var widgets = this.__findWidgets(item.name);
        if (widgets && widgets.widget) {
          allWidgets.push({
            widget : widgets.widget,
            value : item.value
          });
          widgets.widget.addListener("changeValue", listenerCallback);
        }
      }, this);

      if (this.__initialized) {
        // deferred to make sure everything is loaded completely
        (new qx.util.DeferredCall(listenerCallback, this)).schedule();
      }
      else {
        this.addListenerOnce("initialized", listenerCallback);
      }
    }
  },

  destruct : function() {
    this.__object = null;
    this.__widget = null;
  }
});