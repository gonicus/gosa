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
 * Controller for the {@link gosa.ui.widget.ObjectEdit} widget; connects it to the model.
 */
qx.Class.define("gosa.data.controller.ObjectEdit", {
  extend : gosa.data.controller.BaseObjectEdit,
  implement: gosa.data.controller.IObject,

  /**
   * @param obj {gosa.proxy.Object}
   * @param widget {gosa.ui.widgets.ObjectEdit}
   */
  construct : function(obj, widget) {
    this.base(arguments);
    qx.core.Assert.assertInstance(obj, gosa.proxy.Object);
    qx.core.Assert.assertInstance(widget, gosa.ui.widgets.ObjectEdit);

    this.__object = obj;
    this._widget = widget;
    this._changeValueListeners = {};
    this._validatingWidgets = [];
    this._connectedAttributes = [];
    this.__extensionFinder = new gosa.data.util.ExtensionFinder(obj);
    this.__extensionController = new gosa.data.controller.Extensions(obj, this);
    this.__backendChangeController = new gosa.data.controller.BackendChanges(obj, this);
    this.__modelWidgetConnector = new gosa.data.ModelWidgetConnector(this.__object, this._widget);
    this.__modificationManager = new gosa.data.ModificationManager(this.__object);

    this.__modificationManager.bind("modified", this, "modified");
    this.__object.attributes.forEach(this.__modificationManager.registerAttribute, this.__modificationManager);

    this.__backendChangeController.addListener("silentlyMerged", function(ev) {
      ev.getData().forEach(this.__modificationManager.updateAttribute, this.__modificationManager);
    }, this);

    this._addListenersToAllContexts();
    this.__setUpWidgets();

    obj.addListener(
      "foundDifferencesDuringReload",
      this.__backendChangeController.onFoundDifferenceDuringReload,
      this.__backendChangeController
    );

    this.__object.setUiBound(true);
    this._initialized = true;
    this.fireEvent("initialized");

    this.__extensionController.checkForMissingExtensions();

    obj.addListener("closing", this._onObjectClosing, this);
    obj.addListener("removed", this.__onObjectRemove, this);
  },

  events : {
    /**
     * Fired when all setup etc. is done.
     */
    "initialized" : "qx.event.type.Event"
  },

  members : {
    __object : null,
    _changeValueListeners : null,
    _initialized : false,
    _validatingWidgets : null,
    _connectedAttributes : null,
    _globalObjectListenersSet : false,
    __extensionController : null,
    __backendChangeController : null,
    __extensionFinder : null,
    __modelWidgetConnector : null,
    __modificationManager : null,

    getObject: function() {
      return this.__object;
    },

    getObjectData: function() {
      var data = {};
      this.__object.attributes.forEach(function(attributeName) {
        var arr = this.__object.get(attributeName);
        if (arr instanceof qx.data.Array && arr.getLength() === 1) {
          data[attributeName] = arr.getItem(0);
        }
      }, this);
      return data;
    },

    closeWidgetAndObject : function() {
      this._widget.close();
      this.closeObject();
    },

    closeObject : function() {
      if (this.__object && !this.__object.isDisposed() && !this.__object.isClosed()) {
        this.__object.setUiBound(false);
        return this.__object.close()
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error).open();
        });
      }
    },

    saveObject : function() {
      if (!this.isModified()) {
        this.__object.setUiBound(false);
        this.closeObject();
        return;
      }

      if (!this.isValid()) {
        console.warn("TODO: Invalid values detected");
        return;
      }

      return this.__object.commit()
      .catch(function(exc) {
        var error = exc.getData ? exc.getData() : exc;
        var widget = null;
        this.setValid(false);
        if (error.topic) {
          // create all extension tabs until widget has been found
          var widgetBuddyTuple = this._findWidgets(error.topic, true);
          if (widgetBuddyTuple) {
            widget = widgetBuddyTuple.widget;
            // open tab with widget
            this._widget.openTab(widgetBuddyTuple.context);
          }
        }
        if (widget) {
          this.__showWidgetError(widget, error);
          throw exc;
        } else {
          gosa.ui.dialogs.Error.show(exc);
          throw exc;
        }
      }, this)
      .then(function() {
        this.__object.setUiBound(false);
        return this.closeObject();
      }, this);
    },

    __onObjectRemove : function() {
      this._widget.close();

      var dialog = new gosa.ui.dialogs.Info(qx.locale.Manager.tr("The object was automatically closed because it was removed in the backend."));
      dialog.setAutoDispose(true);
      dialog.open();
    },

    /**
     * Calls the method on the object.
     *
     * @param methodName {String} The method to call
     * @param args {Array ? null} Arguments to pass to that function
     */
    callObjectMethod : function(methodName, args) {
      qx.core.Assert.assertString(methodName);
      qx.core.Assert.assertFunction(this.__object[methodName]);

      return this.__object[methodName].apply(this.__object, args);
    },

    /**
     * Forward to {@link gosa.ui.widgets.ObjectEdit#addDialog}.
     */
    addDialog : function(dialog) {
      this._widget.addDialog(dialog);
    },

    /**
     * @return {gosa.data.controller.Extensions}
     */
    getExtensionController : function() {
      return this.__extensionController;
    },

    /**
     * @return {gosa.data.util.ExtensionFinder}
     */
    getExtensionFinder : function() {
      return this.__extensionFinder;
    },

    /**
     * @return {gosa.data.controller.Actions}
     */
    getActionController : function() {
      if (!this._actionController) {
        this._actionController =  new gosa.data.controller.Actions(this.__object);
      }
      return this._actionController;
    },

    /**
     * Returns all extensions which are currently active on the object.
     *
     * @return {Array} List of extension names (strings); might be empty
     */
    getActiveExtensions : function() {
      var result = [];
      var allExts = this.__object.extensionTypes;

      for (var ext in allExts) {
        if (allExts.hasOwnProperty(ext) && allExts[ext]) {
          result.push(ext);
        }
      }
      return result;
    },

    /**
     * @param name {String} Extension name
     * @return {gosa.engine.Context | null}
     */
    getContextByExtensionName : function(name) {
      qx.core.Assert.assertString(name);

      return this._widget.getContexts().find(function(context) {
        return context.getExtension() === name;
      });
    },

    /**
     * @return {String | null} The base type of the object; null if unkown
     */
    getBaseType : function() {
      return this.__object.baseType || null;
    },

    /**
     * @return {Array | null} List of all attributes of the object
     */
    getAttributes : function() {
      return qx.lang.Type.isArray(this.__object.attributes) ? this.__object.attributes : null;
    },

    addContext : function(context) {
      this._addListenerToContext(context);
      this.__setUpWidgets();
    },

    handleTemporaryContext : function(context) {
      if (context.isAppeared()) {
        this.__setUpTemporaryContext(context);
      }
      else {
        context.addListenerOnce("widgetsCreated", function() {
          this.__setUpTemporaryContext(context);
        }, this);
      }
    },

    /**
     * Check the widgets validity for the given context
     *
     * @param context {gosa.engine.Context}
     * @return {boolean}
     */
    checkValidity : function(context) {
      var valid = true;
      if (context) {
        var contextWidgets = context.getWidgetRegistry().getMap();
        for (var modelPath in contextWidgets) {
          if (contextWidgets.hasOwnProperty(modelPath)) {
            var widget = contextWidgets[modelPath];
            valid = valid && (this._validatingWidgets.indexOf(widget) === -1 || widget.isValid() || widget.isBlocked());
          }
        }
      }
      return valid;
    },

    __setUpTemporaryContext : function(context) {
      gosa.util.Object.iterate(context.getWidgetRegistry().getMap(), function(attributeName, widget) {
        this.__modelWidgetConnector.connect(attributeName, this.__object.attribute_data[attributeName], widget);
        this.__addModifyListeners(attributeName, widget, true);
      }, this);
    },

    /**
     * Called when the event {@link gosa.proxy.Object#closing} is sent.
     */
    _onObjectClosing : function(event) {
      var data = event.getData();

      if (data.uuid !== this.__object.uuid) {
        return;
      }

      switch (data.state) {
        case "closing":
          this._widget.onClosing(this.__object.dn, parseInt(data.minutes));
          break;
        case "closing_aborted":
          this._widget.closeCloseDialog();
          break;
        case "closed":
          this.__object.setClosed(true);
          this._widget.onClosed();
          break;
      }
    },

    /**
     * Invoke rpc to continue editing while the timeout for automatic closing is running.
     */
    continueEditing : function() {
      gosa.io.Rpc.getInstance().cA("continueObjectEditing", this.__object.instance_uuid);
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

      var extensions = templateObjects.map(function(tmpl) {
        return tmpl.extension;
      });

      var contexts = this._widget.getContexts().filter(function(context) {
        return qx.lang.Array.contains(extensions, context.getExtension());
      });

      if (contexts.length) {
        contexts.forEach(function (context) {
          var map = context.getWidgetRegistry().getMap();
          var widget;

          for (var key in map) {
            if (map.hasOwnProperty(key)) {
              widget = map[key];
              if (widget.isEnabled() && !widget.isBlocked()) {
                widget.enforceUpdateOnServer();
              }
            }
          }
        });
      }
      else {
        templateObjects.forEach(function(templateObject) {
          this._widget.addTab(templateObject);
        }, this);
      }
    },

    _addListenersToAllContexts : function() {
      this._widget.getContexts().forEach(this._addListenerToContext, this);
    },

    _addListenerToContext : function(context) {
      if (!context.isAppeared()) {
        context.addListenerOnce("widgetsCreated", this.__setUpWidgets, this);
      }
    },

    __setUpWidgets : function() {
      this.__modelWidgetConnector.connectAll();

      if (!this._globalObjectListenersSet) {
        this.__object.addListener("propertyUpdateOnServer", this._onPropertyUpdateOnServer, this);
        this._globalObjectListenersSet = true;
      }

      this.__addModifyListenersForAllContexts();
    },

    __addModifyListenersForAllContexts : function() {
      this._widget.getContexts().forEach(function(context) {
        gosa.util.Object.iterate(context.getWidgetRegistry().getMap(), this.__addModifyListeners, this);
      }, this);
    },

    __addModifyListeners : function(modelPath, widget, temporary) {
      if (qx.lang.Array.contains(this._connectedAttributes, modelPath)) {
        return;
      }
      var listenerId = widget.addListener("changeValue", this._onChangeWidgetValue, this);
      widget[listenerId] = widget;

      if (widget instanceof gosa.ui.widgets.Widget) {
        this._validatingWidgets.push(widget);
      }

      if (!temporary) {
        this._connectedAttributes.push(modelPath);
      }
    },

    /**
     * Finds the widget and its buddy label for the given name (model path).
     *
     * @param name {String} The name/model path of the widgets
     * @param createWidgets {Boolean?} if true widgets for context will be created if necessary
     * @return {Object | null} An object in the shape of {widget: <widget>, buddy: <buddy widget>, context: <context>} or null
     */
    _findWidgets : function(name, createWidgets) {
      qx.core.Assert.assertString(name);

      var context;
      var contexts = this._widget.getContexts();

      for (var i = 0; i < contexts.length; i++) {
        context = contexts[i];
        if (createWidgets === true && !context.isAppeared()) {
          context.createWidgets();
        }
        var widgets = context.getWidgetRegistry().getMap();
        for (var modelPath in widgets) {
          if (widgets.hasOwnProperty(modelPath) && modelPath === name) {
            return {
              widget : widgets[modelPath],
              buddy : context.getBuddyRegistry().getMap()[modelPath],
              context : context
            };
          }
        }
      }
      return null;
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
        var attr = event.getTarget().getAttribute();
        this.__object.setAttribute(attr, event.getData());
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
          widget.resetErrorMessage();
        }
      }
      else if (!data.success && data.error) {
        this.__showWidgetError(widget, data.error.getData());
      }
      this._updateValidity();
    },

    __showWidgetError: function(widget, error) {
      if (error.code === "ATTRIBUTE_CHECK_FAILED" || error.code === "ATTRIBUTE_MANDATORY") {
        if (widget) {
          widget.setError(error);
        }
      }
      else {
        new gosa.ui.dialogs.Error(error).open();
      }
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
        return widget.isValid() || widget.isBlocked();
      }));
    }
  },

  destruct : function() {
    this.__object.removeListener("removed", this.__onObjectRemove, this);
    this.__object.removeListener("closing", this._onObjectClosing, this);
    this.__object.removeListener(
      "foundDifferencesDuringReload",
      this.__backendChangeController.onFoundDifferenceDuringReload,
      this.__backendChangeController
    );

    if (this.__object && !this.__object.isDisposed()) {
      this.__object.removeListener("propertyUpdateOnServer", this._onPropertyUpdateOnServer, this);
    }

    this._cleanupChangeValueListeners();
    this.closeObject();

    this._disposeObjects(
      "__extensionFinder",
      "__backendChangeController",
      "__extensionController",
      "__modelWidgetConnector",
      "__modificationManager"
    );

    this.__object = null;
    this._changeValueListeners = null;
    this._validatingWidgets = null;
    this._connectedAttributes = null;
  }
});
