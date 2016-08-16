/**
 * A 'context' is a container for the widgets of a template and different utilities, e.g. widget registries for the
 * widgets and buddies. It also creates the neccessary widets using a widget processor (see
 * {@link gosa.engine.processors.Base} and {@link gosa.engine.ProcessorFactory}).
 */
qx.Class.define("gosa.engine.Context", {
  extend : qx.core.Object,

  /**
   * @param template {Object} A widget template as a object (i.e. already parsed from json)
   * @param rootWidget {qx.ui.container.Composite} The contianer widget where the template widgets will be added to
   */
  construct : function(template, rootWidget) {
    this.base(arguments);
    qx.core.Assert.assertObject(template);
    qx.core.Assert.assertInstance(rootWidget, qx.ui.container.Composite);

    this._template = template;
    this._rootWidget = rootWidget;
    this._widgetRegistry = new gosa.engine.WidgetRegistry();
    this._buddyRegistry = new gosa.engine.WidgetRegistry();
    this._resourceManager = new gosa.engine.ResourceManager();

    this._createWidgets();
  },

  members : {
    _template : null,
    _rootWidget : null,
    _widgetRegistry : null,
    _buddyRegistry : null,
    _resourceManager : null,

    /**
     * @return {gosa.ui.widgets.Widget} The root widget container for this template
     */
    getRootWidget : function() {
      return this._rootWidget;
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

    _createWidgets : function() {
      var processor = gosa.engine.ProcessorFactory.getProcessor(this._template, this);
      processor.process(this._template, this._rootWidget);

      this._connectBuddies();
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
    this._disposeObjects(
      "_rootWidget",
      "_widgetRegistry",
      "_buddyRegistry",
      "_resourceManager"
    );
  }
});
