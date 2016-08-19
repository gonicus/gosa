/**
 * Controller for the {@link gosa.ui.widget.ObjectEdit} widget; connects it to the model.
 */
qx.Class.define("gosa.data.ObjectEditController", {
  extend : qx.core.Object,

  /**
   * @param obj {gosa.proxy.Object}
   * @param widget {gosa.ui.widgets.ObjectEdit}
   */
  construct : function(obj, widget) {
    this.base(arguments);
    qx.core.Assert.assertInstance(obj, gosa.proxy.Object);
    qx.core.Assert.assertInstance(widget, gosa.ui.widgets.ObjectEdit);

    this._obj = obj;
    this._widget = widget;

    this._connectModelWithWidget();
  },

  members : {
    _obj : null,
    _widget : null,

    _currentWidget : null,
    _currentBuddy : null,

    _connectModelWithWidget : function() {
      var o = this._obj;
      var widgets, attribute, widget, buddy;

      for (var name in o.attribute_data) {
        if (o.attribute_data.hasOwnProperty(name)) {
          attribute = o.attribute_data[name];
          widgets = this._findWidgets(name);
          if (widgets === null) {
            qx.log.Logger.warn("No widgets found for '" + name + "'");
            continue;
          }

          if (widgets.hasOwnProperty("widget") && widgets.widget instanceof qx.ui.core.Widget) {
            this._currentWidget = widgets.widget;
          }

          if (widgets.hasOwnProperty("buddy") && widgets.buddy instanceof qx.ui.core.Widget) {
            this._currentBuddy = widgets.buddy;
          }

          // console.log("%s, %O, %O", name, attribute, widgets);
          this._handleProperties(attribute);
        }
      }
    },

    /**
     * Finds the widget and its buddy label for the given name (model path).
     *
     * @param name {String} The name/model path of the widgets
     * @return {Object | null} An object in the shape of {widget: <widget>, buddy: <buddy widget>} or null
     */
    _findWidgets : function(name) {
      qx.core.Assert.assertString(name);

      var context;
      var contexts = this._widget.getContexts();

      for (var i = 0; i < contexts.length; i++) {
        context = contexts[i];
        var widgets = context.getWidgetRegistry().getMap();
        for (var modelPath in widgets) {
          if (widgets.hasOwnProperty(modelPath) && modelPath === name) {
            return {
              widget : widgets[modelPath],
              buddy : context.getBuddyRegistry().getMap()[modelPath]
            };
          }
        }
      }
      return null;
    },

    /**
     * @param attribute {Object}
     */
    _handleProperties : function(attribute) {
      if (attribute.hasOwnProperty("mandatory")) {
        this._setProperty("mandatory", !!attribute.mandatory);
      }
      if (attribute.hasOwnProperty("readonly")) {
        this._setProperty("readOnly", !!attribute.readonly);
      }
      if (attribute.hasOwnProperty("blocked_by")) {
        this._handleBlockedBy(attribute.blocked_by);
      }
    },

    _setProperty : function(propertyName, value) {
      if (this._currentWidget) {
        this._currentWidget.set(propertyName, value);
      }
      if (this._currentBuddy) {
        this._currentBuddy.set(propertyName, value);
      }
    },

    _handleBlockedBy : function(value) {
      if (value.length === 0) {
        return;
      }
      var allWidgets = [];

      var listenerCallback = function() {
        var block = allWidgets.every(function(item) {
          console.log("%O, %O", item.widget.getValue(), item.value);
          return item.widget.getValue() === item.value;
        });

        console.log(block);
      };

      value.forEach(function(item) {
        var widgets = this._findWidgets(item.name);
        if (widgets && widgets.widget) {
          allWidgets.push({
            widget : widgets.widget,
            value : item.value
          });
          widgets.widget.addListener("changeValue", listenerCallback);
        }
      }, this);
      listenerCallback();
    }
  },

  destruct : function() {
    this._obj = null;
    this._widget = null;
  }
});
