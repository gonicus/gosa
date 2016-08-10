qx.Class.define("gosa.engine.processors.WidgetProcessor", {
  extend : gosa.engine.processors.Base,

  construct : function(context){
    this._context = context;
    this.base(arguments);
  },

  members : {
    _context : '',

    process : function(node, target) {
      if (this._getValue(node, "class")) {
        var widget = this._createAndAddWidget(node, target);
        this._handleLayout(node, widget);
        this._handleProperties(node, widget);
        this._createAndAddChildren(node, widget);
      }
      else if (this._getValue(node, "form")) {
        this._includeForm(node, target);
      }
    },

    _createAndAddWidget : function(node, target) {
      var clazz = qx.Class.getByName(this._getValue(node, "class"));
      qx.core.Assert.assertNotUndefined(clazz, "Unknown class: '" + this._getValue(node, "class") + "'");

      var widget = new clazz();
      if (!target) {
        target = this.getTarget();
        gosa.engine.WidgetRegistry.getInstance().addWidget(this._context, target);
      }
      target.add(widget, this._getValue(node, "addOptions"));
      this._handleExtensions(node, widget);

      var modelPath = this._getValue(node, "modelPath");
      if(modelPath){
        gosa.engine.WidgetRegistry.getInstance().addBuddy(this._context, modelPath, widget);
      }
      gosa.engine.WidgetRegistry.getInstance().addWidget(this._context, widget);

      var buddyModelPath = this._getValue(node, "buddyModelPath");
      if(buddyModelPath){
        gosa.engine.WidgetRegistry.getInstance().addMate(this._context, buddyModelPath, widget);
      }

      return widget;
    },

    _createAndAddChildren : function(node, target) {
      var children = this._getValue(node, "children");
      if (children) {
        children.forEach(function(child) {
          this.process(child, target);
        }, this);
      }
    },

    _handleLayout : function(node, target) {
      var layout = this._getValue(node, "layout");
      if (layout) {
        var clazz = qx.Class.getByName(layout);
        var instance = new clazz();

        var layoutConfig = this._getValue(node, "layoutConfig");
        if (layoutConfig) {
          instance.set(layoutConfig);
        }
        target.setLayout(instance);
      }
    },

    _handleProperties : function(node, target) {
      var properties = this._getValue(node, "properties");
      if (properties) {
        var transformedProperties = this._transformProperties(properties);
        
        for(var property in transformedProperties){
          if(qx.Class.hasProperty(target.constructor, property)){
            target.set(property, transformedProperties[property]);
          } else {
            qx.log.Logger.warn('Property: ' + property + ' not available on target widget: '+ target.basename);
            target[property] = transformedProperties[property];
          }
        }
      }
    },

    _includeForm : function(node, target) {
      var form = this._resolveSymbol(this._getValue(node, "form"));
      target.add(form, this._getValue(node, "addOptions"));
    }
  }
});
