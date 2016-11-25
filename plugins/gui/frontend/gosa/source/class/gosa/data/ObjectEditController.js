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
    this._changeValueListeners = {};
    this._validatingWidgets = [];
    this._connectedAttributes = [];
    this._extensionController = new gosa.data.ExtensionController(obj, this);

    this._addListenersToAllContexts();
    this._setUpWidgets();

    this._widget.addListener("contextAdded", this._onContextAdded, this);

    this._obj.setUiBound(true);
    this._initialized = true;
    this.fireEvent("initialized");

    obj.addListener("closing", this._onObjectClosing, this);
  },

  events : {
    /**
     * Fired when all setup etc. is done.
     */
    "initialized" : "qx.event.type.Event"
  },

  properties : {
    modified : {
      check : "Boolean",
      init : false,
      event : "changeModified"
    },

    valid : {
      check : "Boolean",
      init : true,
      event : "changeValid"
    }
  },

  members : {
    _obj : null,
    _widget : null,
    _changeValueListeners : null,
    _currentWidget : null,
    _currentBuddy : null,
    _initialized : false,
    _validatingWidgets : null,
    _connectedAttributes : null,
    _globalObjectListenersSet : false,
    _extensionController : null,

    closeObject : function() {
      if (this._obj && !this._obj.isDisposed() && !this._obj.isClosed()) {
        this._obj.setUiBound(false);
        this._obj.close()
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error.message).open();
        });
      }
    },

    saveObject : function() {
      if (!this.isModified()) {
        this._obj.setUiBound(false);
        this.closeObject();
        return;
      }

      if (!this.isValid()) {
        console.warn("TODO: Invalid values detected");
        return;
      }

      this._obj.setUiBound(false);
      this._obj.commit()
      .then(this.closeObject, this)
      .catch(function(error) {
        this.error(error);
        this.error(error.message);
        this.error(error.topic);
        this.error(error.code);
        this.error(error.details);
        new gosa.ui.dialogs.Error(error.message).open();
      }, this);
    },

    /**
     * Calls the method on the object.
     *
     * @param methodName {String} The method to call
     * @param args {Array ? null} Arguments to pass to that function
     */
    callObjectMethod : function(methodName, args) {
      qx.core.Assert.assertString(methodName);
      qx.core.Assert.assertFunction(this._obj[methodName]);

      return this._obj[methodName].apply(this._obj, args);
    },

    /**
     * Exposes the object (model of the controller). Thee shall not use it in views...
     *
     * @return {gosa.proxy.Object | null}
     */
    getObject : function() {
      return this._obj;
    },

    /**
     * Returns all extensions which are currently active on the object.
     *
     * @return {Array} List of extension names (strings); might be empty
     */
    getActiveExtensions : function() {
      var result = [];
      var allExts = this._obj.extensionTypes;

      for (var ext in allExts) {
        if (allExts.hasOwnProperty(ext) && allExts[ext]) {
          result.push(ext);
        }
      }
      return result;
    },

    /**
     * Removes the extension from the object in that its tab page(s) won't be shown any more.
     *
     * @param extension {String} Name of the extension (e.g. "SambaUser")
     */
    removeExtension : function(extension) {
      qx.core.Assert.assertString(extension);
      this._extensionController.removeExtension(extension);
    },

    /**
     * Adds the stated extension to the object.
     *
     * @param extension {String}
     */
    addExtension : function(extension) {
      qx.core.Assert.assertString(extension);
      this._extensionController.addExtension(extension);

      this._widget.getContexts().forEach(function(context) {
        if (context.getExtension() === extension) {
          console.log(context);
        }
      });
    },

    /**
     * Returns a list of extensions that the object can be extended by.
     *
     * @return {Array} List of extension names (as strings); might be empty
     */
    getExtendableExtensions : function() {
      return this._extensionController.getExtendableExtensions();
    },

    /**
     * Returns a list of extensions that can be retracted from the object.
     *
     * @return {Array} List of extension names (as strings); might be empty
     */
    getRetractableExtensions : function() {
      return this._extensionController.getRetractableExtensions();
    },

    /**
     * @return {String | null} The base type of the object; null if unkown
     */
    getBaseType : function() {
      return this._obj.baseType || null;
    },

    /**
     * @return {Array | null} List of all attributes of the object
     */
    getAttributes : function() {
      return qx.lang.Type.isArray(this._obj.attributes) ? this._obj.attributes : null;
    },

    /**
     * Called when the event {@link gosa.proxy.Object#closing} is sent.
     */
    _onObjectClosing : function(event) {
      var data = event.getData();

      // TODO: How can this happen?
      if (data.uuid !== this._obj.uuid) {
        return;
      }

      switch (data.state) {
        case "closing":
          this._widget.onClosing(this._obj.dn, parseInt(data.minutes));
          break;
        case "closing_aborted":
          this._widget.onClosingAborted();
          break;
        case "closed":
          this._widget.onClosed();
          break;
      }
    },

    /**
     * Invoke rpc to continue editing while the timeout for automatic closing is running.
     */
    continueEditing : function() {
      gosa.io.Rpc.getInstance().cA("continueObjectEditing", this._obj.instance_uuid);
    },

    /**
     * Removes the tab page (widget only!) for the given extension.
     *
     * @param extension {String} Name of the extension, e.g. SambaUser
     */
    removeExtensionTab : function(extension) {
      qx.core.Assert.assertString(extension);

      // find all matching contexts (could be several for one extension)
      var contexts = this._widget.getContexts().filter(function(context) {
        return context.getExtension() === extension;
      });

      contexts.forEach(function(context) {
        this._widget.removeTab(context.getRootWidget());
      }, this);
    },

    /**
     * Adds tab pages (widget only) for the given extension.
     *
     * @param templateObjects {Array}
     */
    addExtensionTabs : function(templateObjects) {
      qx.core.Assert.assertArray(templateObjects);
      templateObjects.forEach(function(templateObject) {
        this._widget.addTab(templateObject);
      }, this);
    },

    _addListenersToAllContexts : function() {
      this._widget.getContexts().forEach(this._addListenerToContext, this);
    },

    _addListenerToContext : function(context) {
      if (!context.isAppeared()) {
        context.addListenerOnce("widgetsCreated", this._setUpWidgets, this);
      }
    },

    _setUpWidgets : function() {
      this._connectModelWithWidget();
      this._addModifyListeners();
    },

    _connectModelWithWidget : function() {
      var o = this._obj;
      var widgets, attribute;

      for (var name in o.attribute_data) {
        if (o.attribute_data.hasOwnProperty(name)) {

          if (qx.lang.Array.contains(this._connectedAttributes, name)) {
            continue;
          }

          attribute = o.attribute_data[name];
          widgets = this._findWidgets(name);
          if (widgets === null) {
            continue;
          }

          if (widgets.hasOwnProperty("widget") && widgets.widget instanceof qx.ui.core.Widget) {
            this._currentWidget = widgets.widget;
          }
          else {
            this._currentWidget = null;
          }

          if (widgets.hasOwnProperty("buddy") && widgets.buddy instanceof qx.ui.core.Widget) {
            this._currentBuddy = widgets.buddy;
          }
          else {
            this._currentBuddy = null;
          }

          this._handleProperties(attribute);
          this._currentWidget.setValue(o.get(name));

          // binding from widget to model
          this._currentWidget.bind("value", o, name);
        }
      }

      if (!this._globalObjectListenersSet) {
        o.addListener("propertyUpdateOnServer", this._onPropertyUpdateOnServer, this);
        this._globalObjectListenersSet = true;
      }
    },

    _addModifyListeners : function() {
      this._widget.getContexts().forEach(function(context) {
        var widgets = context.getWidgetRegistry().getMap();
        var widget, listenerId;
        for (var modelPath in widgets) {
          if (qx.lang.Array.contains(this._connectedAttributes, modelPath)) {
            continue;
          }

          if (widgets.hasOwnProperty(modelPath)) {
            widget = widgets[modelPath];
            listenerId = widget.addListener("changeValue", this._onChangeWidgetValue, this);
            widget[listenerId] = this._currentWidget;

            // check validity
            if (widget instanceof gosa.ui.widgets.Widget) {
              this._validatingWidgets.push(widget);
            }

            this._connectedAttributes.push(modelPath);
          }
        }
      }, this);
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
      var setValue = {};

      if (attribute.hasOwnProperty("mandatory")) {
        setValue.mandatory = !!attribute.mandatory;
      }
      if (attribute.hasOwnProperty("readonly")) {
        setValue.readOnly = !!attribute.readonly;
      }
      if (attribute.hasOwnProperty("multivalue")) {
        setValue.multivalue = !!attribute.multivalue;
      }
      if (attribute.hasOwnProperty("default")) {
        setValue.defaultValue = attribute["default"];
      }
      if (attribute.hasOwnProperty("type")) {
        setValue.type = attribute.type;
      }
      if (attribute.hasOwnProperty("case_sensitive")) {
        setValue.caseSensitive = attribute.case_sensitive;
      }
      if (attribute.hasOwnProperty("unique")) {
        setValue.unique = attribute.unique;
      }
      if (attribute.hasOwnProperty("depends_on")) {
        setValue.dependsOn = attribute.depends_on;
      }
      if (attribute.hasOwnProperty("values")) {
        setValue.values = attribute.values;
      }

      if (this._currentWidget) {
        this._currentWidget.set(setValue);
      }
      if (this._currentBuddy) {
        this._currentBuddy.set(setValue);
      }


      if (attribute.hasOwnProperty("blocked_by")) {
        this._handleBlockedBy(attribute.blocked_by);
      }
    },

    _handleBlockedBy : function(value) {
      if (value.length === 0) {
        return;
      }
      var allWidgets = [];
      var currentBuddy = this._currentBuddy;
      var currentWidget = this._currentWidget;

      var listenerCallback = function() {
        var block = allWidgets.every(function(item) {
          var value = item.widget.getValue();
          if (value instanceof qx.data.Array && value.getLength() > 0) {
            value = value.getItem(0);
          }
          return value === item.value;
        });

        if (block) {
          if (currentBuddy) {
            currentBuddy.block();
          }
          if (currentWidget) {
            currentWidget.block();
          }
        }
        else {
          if (currentBuddy) {
            currentBuddy.unblock();
          }
          if (currentWidget) {
            currentWidget.unblock();
          }
        }
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

      if (this._initialized) {
        // deferred to make sure everything is loaded completely
        (new qx.util.DeferredCall(listenerCallback, this)).schedule();
      }
      else {
        this.addListenerOnce("initialized", listenerCallback);
      }
    },

    /**
     * @param event {qx.event.type.Data}
     */
    _onChangeWidgetValue : function(event) {
      if (!this._initialized) {
        return;
      }
      qx.core.Assert.assertInstance(event, qx.event.type.Data);

      if (!event.getData().getUserData("initial")) {
        this.setModified(true);
        var attr = event.getTarget().getAttribute();
        this._obj.setAttribute(attr, event.getData());
      }
    },

    /**
     * Called when the event "propertyUpdateOnServer" is fired on the object.
     *
     * @param event {qx.event.type.Data}
     */
    _onPropertyUpdateOnServer : function(event) {
      var data = event.getData();
      var widget = null;
      if (data.property) {
        widget = this._validatingWidgets.find(function(widget) {
          return widget instanceof gosa.ui.widgets.Widget && widget.getAttribute() === data.property;
        });
      }

      if (data.success) {
        if (widget) {
          widget.setValid(true);
        }
      }
      else if (!data.success && data.error) {
        if (data.error.code === "ATTRIBUTE_CHECK_FAILED" || data.error.code === "ATTRIBUTE_MANDATORY") {
          if (widget) {
            widget.setInvalidMessage(data.error.message);
            widget.setValid(false);
          }
        }
        else {
          new gosa.ui.dialogs.Error(data.error.message).open();
        }
      }
      this._updateValidity();
    },

    _cleanupChangeValueListeners : function() {
      for (var id in this._changeValueListeners) {
        if (this._changeValueListeners.hasOwnProperty(id)) {
          if (!this._changeValueListeners[id].isDisposed()) {
            this._changeValueListeners[id].removeListenerById(id);
          }
        }
      }
      this._changeValueListeners = {};
    },

    _updateValidity : function() {
      this.setValid(this._validatingWidgets.every(function(widget) {
        return widget.isValid();
      }));
    },

    /**
     * @param event {qx.event.type.Data}
     */
    _onContextAdded : function(event) {
      this._addListenerToContext(event.getData());
      this._setUpWidgets();
    }
  },

  destruct : function() {
    this._obj.removeListener("closing", this._onObjectClosing, this);
    this._widget.removeListener("contextAdded", this._onContextAdded, this);

    if (this._obj && !this._obj.isDisposed()) {
      this._obj.removeListener("propertyUpdateOnServer", this._onPropertyUpdateOnServer, this);
    }

    this._cleanupChangeValueListeners();
    this.closeObject();

    this._disposeObjects("_extensionController");

    this._obj = null;
    this._widget = null;
    this._changeValueListeners = null;
    this._validatingWidgets = null;
    this._connectedAttributes = null;
  }
});
