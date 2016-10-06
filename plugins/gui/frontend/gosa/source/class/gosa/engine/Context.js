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
   * @param extension {String} Name of the extension this context creates widgets for (e.g. "PosixUser")
   * @param attributes {Array} Names of all attributes that are in the object
   */
  construct : function(template, rootWidget, extension, attributes) {
    this.base(arguments);
    qx.core.Assert.assertObject(template);
    qx.core.Assert.assertQxWidget(rootWidget);
    qx.core.Assert.assertArray(attributes);

    if (extension !== undefined && extension !== null) {
      qx.core.Assert.assertString(extension);
    }

    this._template = template;
    this._rootWidget = rootWidget;
    this._extension = extension;
    this._attributes = attributes;
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

  members : {
    _processor : null,
    _template : null,
    _rootWidget : null,
    _extension : null,
    _attributes : null,
    _widgetRegistry : null,
    _buddyRegistry : null,
    _resourceManager : null,
    _actionMenuEntries : null,
    _appeared : false,

    /**
     * @return {gosa.ui.widgets.Widget} The root widget container for this template
     */
    getRootWidget : function() {
      return this._rootWidget;
    },

    getExtension : function() {
      return this._extension;
    },

    /**
     * @return {Array} Names of all attributes that are in the object
     */
    getAttributes : function() {
      return this._attributes;
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
      this._processor.process(this._template, this._rootWidget);
      this._connectBuddies();
      this._appeared = true;
      this.fireDataEvent("widgetsCreated", this);
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
    this._disposeObjects(
      "_processor",
      "_rootWidget",
      "_widgetRegistry",
      "_buddyRegistry",
      "_resourceManager"
    );
  }
});
