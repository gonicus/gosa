/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.engine.processors.WidgetProcessor", {
  extend : gosa.engine.processors.Base,

  statics : {

    /**
     * @type {Array} Properties on widgets in the template that shall be ignored
     */
    IGNORED_PROPERTIES : [
      "categoryTitle"
    ]
  },

  members : {
    _context : null,
    _firstLevelExtensionsProcessed : false,

    process : function(node, target) {
      if (this._getValue(node, "class")) {
        if (this._shallGenerateWidget(node)) {
          var widget = this._createAndAddWidget(node, target);
          this._firstLevelExtensionsProcessed = false;
          this._createAndAddChildren(node, widget);
        }
      }
      else if (this._getValue(node, "form")) {
        this._includeForm(node, target);
      }
    },

    processFirstLevelExtensions : function(node, target) {
      if (this._getValue(node, "class")) {
        this._firstLevelExtensionsProcessed = true;
        this._handleExtensions(node, target);
      }
    },

    /**
     * Checks if the widget should be generated.
     *
     * @param node {Object}
     * @return {Boolean}
     */
    _shallGenerateWidget : function(node) {
      // check if attribute is in object description so it can at least be read
      var modelPath = this._getValue(node, "modelPath") || this._getValue(node, "buddyModelPath");
      if (modelPath && !qx.lang.Array.contains(this._context.getAttributes(), modelPath)) {
        return false;
      }

      // check rpc permission for dialogs
      if (qx.lang.Type.isObject(node.properties) && qx.lang.Type.isString(node.properties.dialog)) {
        var sessionObj = gosa.Session.getInstance();
        if (!gosa.util.Template.getDialogRpc(node.properties.dialog).every(sessionObj.isCommandAllowed, sessionObj)) {
          return false;
        }
      }

      return true;
    },

    _createAndAddWidget : function(node, target) {
      var clazz = qx.Class.getByName(this._getValue(node, "class"));
      qx.core.Assert.assertNotUndefined(clazz, "Unknown class: '" + this._getValue(node, "class") + "'");

      var widget = new clazz();
      target.add(widget, this._getValue(node, "addOptions"));

      this._handleLayout(node, widget);
      this._handleProperties(node, widget);

      if (!this._firstLevelExtensionsProcessed) {
        this._handleExtensions(node, widget);
      }

      var modelPath = this._getValue(node, "modelPath");
      if (widget instanceof gosa.ui.widgets.Widget) {
        if (this._context.getExtension()) {
          widget.setExtension(this._context.getExtension());
        }
        if (modelPath) {
          widget.setAttribute(modelPath);
        }
      }

      // register widget
      if (modelPath) {
        this._context.getWidgetRegistry().addWidget(modelPath, widget);
      }

      var buddyModelPath = this._getValue(node, "buddyModelPath");
      if (buddyModelPath) {
        this._context.getBuddyRegistry().addWidget(buddyModelPath, widget);
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

        for (var property in transformedProperties) {
          if (qx.lang.Array.contains(this.self(arguments).IGNORED_PROPERTIES, property)) {
            break;
          }
          if (qx.Class.hasProperty(target.constructor, property)) {
            target.set(property, transformedProperties[property]);
          }
          else {
            qx.log.Logger.warn('Property: ' + property + ' not available on target widget: ' + target.basename);
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
