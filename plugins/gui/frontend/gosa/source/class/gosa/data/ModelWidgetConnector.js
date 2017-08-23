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
    __vulid: null,

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

      if (this.__vulid) {
        gosa.io.Sse.getInstance().removeListenerById(this.__vulid);
      }
      this.__vulid = gosa.io.Sse.getInstance().addListener("ObjectPropertyValuesChanged", this._onValuesUpdate, this);

      if (!this.__initialized) {
        this.__initialized = true;
        this.fireEvent("initialized");
      }
    },

    connect : function(attributeName, config, widget, buddy) {
      this.__handleProperties(config, widget, buddy);

      // handle values_inherited from
      if (config.hasOwnProperty("value_inherited_from") && widget && config["value_inherited_from"]) {
        this.__inheritValue(attributeName, widget, config["value_inherited_from"]);
        widget.addListener("appear", function() {
          this.__inheritValue(attributeName, widget, config["value_inherited_from"]);
        }, this);
      }

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
        if (this.__widget.validate) {
          this.__widget.validate();
        }
        else if (this.__widget.getController) {
          this.__widget.getController().checkValidity();
        }
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
        setMap.placeholder = config["default"];
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
      if (config["value_inherited_from"]) {
        setMap.valueInheritedFrom = config.value_inherited_from;
      }

      // set properties
      if (widget) {
        widget.set(setMap);
      }
      if (buddy) {
        buddy.set(setMap);
      }

      // handle values_populate
      if (config["values_populate"] && widget) {
        this.__populateValues(widget, config["values_populate"]);
        widget.addListener("appear", function() {
          this.__populateValues(widget, config["values_populate"]);
        }, this);
      }
    },

    __inheritValue: function(attributeName, widget, config) {
      var reference_value = null;
      var arr = this.__object.get(config["reference_attribute"]);
      if (arr instanceof qx.data.Array && arr.getLength() === 1) {
        reference_value = arr.getItem(0);
      }
      if (reference_value !== null) {
        gosa.io.Rpc.getInstance().cA("**" + config["rpc"], reference_value).then(function(values) {
          if (values[attributeName]) {
            if (widget.setWidgetValue) {
              widget.setWidgetValue(0, values[attributeName]);
            }
            else {
              widget.setValue(new qx.data.Array([values[attributeName]]));
            }
          }
        }, this);
      }
    },

    __populateValues : function(widget, rpcMethod) {
      var data = {};
      this.__object.attributes.forEach(function(attributeName) {
        var arr = this.__object.get(attributeName);
        if (arr instanceof qx.data.Array && arr.getLength() === 1) {
          data[attributeName] = arr.getItem(0);
        }
      }, this);

      var oldValue = widget.getValue() instanceof qx.data.Array && widget.getValue().getLength() > 0
                     ? widget.getValue().getItem(0)
                     : null;

      // get suggested values from backend
      gosa.io.Rpc.getInstance().cA("**"+rpcMethod, data).then(function(suggestions) {
        widget.setValues(suggestions);
        if (oldValue && suggestions.hasOwnProperty(oldValue) || qx.lang.Type.isArray(suggestions) && qx.lang.Array.contains(suggestions, oldValue)) {
          widget.setWidgetValue(0, oldValue);
        }
      });
    },

    /**
     * Backend notifies us that the values of an property have changed
     * @param ev {Event}
     * @protected
     */
    _onValuesUpdate: function(ev) {
      var data = ev.getData();
      if (this.__object.uuid === data.UUID || this.__object.dn === data.DN) {
        data.Change.forEach(function(change) {
          var widget = this.__findWidgets(change.PropertyName).widget;
          var oldValue = widget.getValue() instanceof qx.data.Array && widget.getValue().getLength() > 0
                          ? widget.getValue().getItem(0)
                          : null;
          var suggestions = qx.lang.Json.parse(change.NewValues);
          widget.setValues(suggestions);
          if (oldValue && suggestions.hasOwnProperty(oldValue) || qx.lang.Type.isArray(suggestions) && qx.lang.Array.contains(suggestions, oldValue)) {
            widget.setWidgetValue(0, oldValue);
          }
        }, this);
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

    if (this.__vulid) {
      gosa.io.Sse.getInstance().removeListenerById(this.__vulid);
      this.__vulid = null;
    }
  }
});