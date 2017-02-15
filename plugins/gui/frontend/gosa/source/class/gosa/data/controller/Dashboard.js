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
* Controller for the dashboard widgets.
*/
qx.Class.define("gosa.data.controller.Dashboard", {
  extend : qx.core.Object,
  type: "singleton",

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    __registry: {},
    __parts: {},
    __columns: null,
    __drawn: null,

    /**
     * Register a loaded dashboard widget for usage
     *
     * @param widgetClass {Class} Main widget class
     * @param options {Map} additional configuration options
     */
    registerWidget: function(widgetClass, options) {
      qx.core.Assert.assertTrue(qx.Interface.classImplements(widgetClass, gosa.plugins.IPlugin),
      widgetClass+" does not implement the gosa.plugins.IPlugin interface");
      qx.core.Assert.assertString(options.displayName, "No 'displayName' property found in options");

      var entry = {
        clazz: widgetClass,
        options: options
      };

      var packageName = gosa.util.Reflection.getPackageName(widgetClass);

      var Env = qx.core.Environment;
      var sourceKey = packageName+".source";

      var sourceEnv = Env.get(sourceKey);
      if (!sourceEnv) {
        Env.add(sourceKey, "builtin");
      }

      if (sourceEnv === "part") {
        // plugin loaded from part
        delete this.__parts[packageName];
      }

      this.__registry[packageName] = entry;
    },

    getWidgetRegistry: function() {
      return this.__registry;
    },

    /**
     *
     * @param widget {gosa.plugins.AbstractDashboardWidget} dashboard widget instance
     * @return {Map} the registered widget options
     */
    getWidgetOptions: function(widget) {
      var packageName = gosa.util.Reflection.getPackageName(widget);
      var entry = this.__registry[packageName];
      return entry ? entry.options : {};
    },

    /**
     * Register an (unloaded) part that provides a dashboard widget
     * @param part {qx.ui.part.Part}
     */
    registerPart: function(part) {
      // generate the widget name from the part name
      var widgetName = qx.lang.String.firstUp(part.getName().replace("gosa.plugins.",""));
      qx.core.Environment.add(part.getName()+".source", "part");
      this.__parts[part.getName()] = widgetName;
    },

    getPartRegistry: function() {
      return this.__parts;
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    /**
     * Load a widget plugin part and create the widget afterwards
     * @param partName {String} part to load
     * @return {qx.Promise}
     */
    loadFromPart: function(partName) {
      var part = qx.io.PartLoader.getInstance().getPart(partName);
      return new qx.Promise(function(resolve, reject) {
        switch(part.getReadyState()) {
          case "initialized":
            // load part
            qx.Part.require(partName, function(states) {
              // part is loaded
              if (states[0] === "complete") {
                resolve(partName);
              } else {
                // error loading part
                reject(new Error(this.tr("Error loading part '%1'", partName)))
              }
            }, this);
            break;
          case "complete":
            resolve(partName);
            break;
        }
      }, this);
    },

    /**
     * Load uploaded widget from backend
     * @param namespace {String} namespace of the widget to load
     * @return {qx.Promise}
     */
    loadFromBackend: function(namespace) {
      return new qx.Promise(function(resolve, reject) {
        var loader = new qx.util.DynamicScriptLoader(['/gosa/uploads/widgets/'+namespace+'/'+namespace+".js"]);
        loader.addListenerOnce("ready", function() {
          resolve(namespace);
        }, this);
        loader.addListener('failed',function(e){
          var data = e.getData();
          this.error("failed to load "+data.script);
          reject(new Error(this.tr("Error loading widget '%1'", data.script)))
        });
        loader.start();
      }, this);
    }
  },

  defer: function(statics) {
    // load available plugin-parts
    var parts = qx.io.PartLoader.getInstance().getParts();
    Object.getOwnPropertyNames(parts).forEach(function(partName) {
      if (partName.startsWith("gosa.plugins.")) {
        statics.registerPart(parts[partName]);
      }
    }, this);
  }
});