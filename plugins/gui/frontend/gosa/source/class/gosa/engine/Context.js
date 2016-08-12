/**
 * A 'context' is a container for the widgets of a template and different utilities, e.g. widget registries for the
 * widgets and buddies. It also creates the neccessary widets using a widget processor (see
 * {@link gosa.engine.processors.Base} and {@link gosa.engine.ProcessorFactory}).
 */
qx.Class.define("gosa.engine.Context", {
  extend : qx.core.Object,

  /**
   * @param template {Object} A widget template as a object (i.e. already parsed from json)
   */
  construct : function(template) {
    this.base(arguments);
    qx.core.Assert.assertObject(template);

    this._template = template;
    this._widgetRegistry = new gosa.engine.WidgetRegistry();
    this._buddyRegistry = new gosa.engine.WidgetRegistry();

    this._createWidgets();
  },

  members : {
    _template : null,
    _rootWidget : null,
    _tabPage : null,
    _widgetRegistry : null,
    _buddyRegistry : null,

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

    _createWidgets : function() {
      this._createContainerWidgets();

      var processor = gosa.engine.ProcessorFactory.getProcessor(this._template, this);
      processor.process(this._template, this._tabPage);

      this._connectBuddies();
      this._createButtons();
    },

    _createContainerWidgets : function() {
      // root container
      this._rootWidget = new qx.ui.container.Composite(new qx.ui.layout.VBox());

      // tab view
      var tabView = new gosa.ui.tabview.TabView();
      tabView.getChildControl("bar").setScrollStep(150);
      this._rootWidget.add(tabView, {flex : 1});

      // tab page
      this._tabPage = new qx.ui.tabview.Page();
      this._tabPage.setLayout(new qx.ui.layout.VBox());
      tabView.add(this._tabPage, {edge : 1});
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
    },

    _createButtons : function() {
      var paneLayout = new qx.ui.layout.HBox();
      paneLayout.set({
        spacing: 4,
        alignX : "right",
        alignY : "middle"
      });
      var buttonPane = this._buttonPane = new qx.ui.container.Composite(paneLayout);
      buttonPane.setMarginTop(11);

      this._rootWidget.add(buttonPane);

      var okButton = gosa.ui.base.Buttons.getOkButton();
      okButton.set({
        enabled : false,
        tabIndex : 30000
      });
      okButton.addState("default");
      buttonPane.add(okButton);

      var cancelButton = gosa.ui.base.Buttons.getCancelButton();
      cancelButton.setTabIndex(30001);
      buttonPane.add(cancelButton);
    }
  },

  destruct : function() {
    this._disposeObjects(
      "_tabPage",
      "_rootWidget",
      "_widgetRegistry",
      "_buddyRegistry"
    );
  }
});
