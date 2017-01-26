/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * A 'context' is a container for the widgets of a template and different utilities, e.g. widget registries for the
 * widgets and buddies. It also creates the neccessary widets using a widget processor (see
 * {@link gosa.engine.processors.Base} and {@link gosa.engine.ProcessorFactory}).
 */
qx.Class.define("gosa.engine.Context", {
  extend : qx.core.Object,

  /**
   * @param template {Object} A widget template as a object (i.e. already parsed from json)
   * @param rootWidget {qx.ui.core.Widget} The container widget where the template widgets will be added to
   * @param extension {String ? undefined} Name of the extension this context creates widgets for (e.g. "PosixUser")
   * @param controller {gosa.data.ObjectEditController ? undefined} Main controller for {@link gosa.ui.widgets.ObjectEdit}
   */
  construct : function(template, rootWidget, extension, controller) {
    this.base(arguments);
    qx.core.Assert.assertObject(template);
    qx.core.Assert.assertQxWidget(rootWidget);

    if (extension !== undefined && extension !== null) {
      qx.core.Assert.assertString(extension);
    }
    if (controller) {
      qx.core.Assert.assertInstance(controller, gosa.data.ObjectEditController);
      this._controller = controller;
    }

    this._template = template;
    this._rootWidget = rootWidget;
    this._extension = extension;
    this._actionMenuEntries = {};
    this._widgetRegistry = new gosa.engine.WidgetRegistry();
    this._buddyRegistry = new gosa.engine.WidgetRegistry();
    this._resourceManager = new gosa.engine.ResourceManager();
    this._processor = gosa.engine.ProcessorFactory.getProcessor(this._template, this);

    this._processor.processFirstLevelExtensions(this._template, this._rootWidget);
    rootWidget.addListenerOnce("appear", this._createWidgets, this);
  },

  events : {
    /**
     * The widgets are created lazy just when they need to be shown. In that case, this event is fired. It is only
     * fired once. Data is this object.
     */
    "widgetsCreated" : "qx.event.type.Data"
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    /**
     * Cumulated validity state of all widgets in this context
     */
    valid: {
      check: "Boolean",
      init: true
    }
  },

  members : {
    _processor : null,
    _template : null,
    _rootWidget : null,
    _extension : null,
    _controller : null,
    _widgetRegistry : null,
    _buddyRegistry : null,
    _resourceManager : null,
    _actionMenuEntries : null,
    _appeared : false,
    _actionController : null,

    /**
     * @return {gosa.data.ActionController} The action controller for this context (each has its own)
     */
    getActionController : function() {
      return this._controller.getActionController();
    },

    /**
     * @return {qx.ui.tabview.Page} The root widget container for this template
     */
    getRootWidget : function() {

      var parent = this._rootWidget;
      do {
        if (parent instanceof qx.ui.tabview.Page) {
          return parent;
        }
        parent = parent.getLayoutParent();
      } while (parent);
    },

    getExtension : function() {
      return this._extension;
    },

    /**
     * @return {Array} Names of all attributes that are in the object
     */
    getAttributes : function() {
      return this._controller.getAttributes();
    },

    /**
     * @return {gosa.engine.WidgetRegistry} The registry for regular widgets
     */
    getWidgetRegistry : function() {
      return this._widgetRegistry;
    },

    /**
     * @return {gosa.engine.WidgetRegistry} The registry for buddy widgets (i.e. labels)
     */
    getBuddyRegistry : function() {
      return this._buddyRegistry;
    },

    /**
     * @return {gosa.engine.ResourceManager} The manager for resources (e.g. images)
     */
    getResourceManager : function() {
      return this._resourceManager;
    },

    /**
     * @return {Map} Hash in the shape "name" -> {@link qx.ui.menu.Button}
     */
    getActions : function() {
      return this._actionMenuEntries;
    },

    isAppeared : function() {
      return this._appeared;
    },

    /**
     * Adds a new button to the action menu.
     *
     * @param name {String} Unique identifier of the action
     * @param button {qx.ui.menu.Button} The button for the action
     */
    addActionMenuEntry : function(name, button) {
      qx.core.Assert.assertString(name);
      qx.core.Assert.assertInstance(button, qx.ui.menu.Button);
      qx.core.Assert.assertFalse(
        this._actionMenuEntries.hasOwnProperty(name),
        "There already is an action with the key '" + name + "'"
      );
      this._actionMenuEntries[name] = button;
    },

    _createWidgets : function() {
      if (!this._appeared) { // widgets might have been created by the ObjectEditController in case of error
        this._processor.process(this._template, this._rootWidget);
        this._connectBuddies();
        this._appeared = true;
        this.fireDataEvent("widgetsCreated", this);
      }
    },

    _connectBuddies : function() {
      var buddyMap = this._buddyRegistry.getMap();
      var widgetMap = this._widgetRegistry.getMap();

      for (var modelPath in buddyMap) {
        if (buddyMap.hasOwnProperty(modelPath)) {
          if (widgetMap.hasOwnProperty(modelPath)) {
            buddyMap[modelPath].setBuddy(widgetMap[modelPath]);
          }
        }
      }
    }
  },

  destruct : function() {
    this._actionMenuEntries = null;
    this._controller = null;
    this._disposeObjects(
      "_actionController",
      "_processor",
      "_rootWidget",
      "_widgetRegistry",
      "_buddyRegistry",
      "_resourceManager"
    );
  }
});
