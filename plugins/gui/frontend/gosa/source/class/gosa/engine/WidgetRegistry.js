qx.Class.define("gosa.engine.WidgetRegistry", {
  extend : qx.core.Object,

  construct : function() {
    this.base(arguments);
    this._registry = {};
  },

  members : {
    _registry : null,

    /**
     * Saves a widget in the registry.
     *
     * @param key {String} The key under which the widget shall be saved (e.g. the model path)
     * @param widget {qx.ui.core.Widget} The widget that shall be saved
     */
    addWidget : function(key, widget) {
      qx.core.Assert.assertString(key);
      qx.core.Assert.assertQxWidget(widget);

      if (this._registry.hasOwnProperty(key)) {
        this.error("There is already a widet registered under the key '" + key + "'.");
        return;
      }
      this._registry[key] = widget;
    },

    removeAndDisposeAllWidgets : function() {
      var widget;
      for (var key in this._registry) {
        if (this._registry.hasOwnProperty(key)) {
          widget = this._registry[key];
          if (widget && !widget.isDisposed) {
            widget.dispose();
          }
        }
      }
      this._registry = {};
    }
  },

  destruct : function() {
    this.removeAndDisposeAllWidgets();
    this._disposeObjects("_registry");
  }
});
