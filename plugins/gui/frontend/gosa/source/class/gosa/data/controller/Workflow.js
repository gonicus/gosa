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
 * Controller for the {@link gosa.ui.widget.WorkflowWizard} widget; connects it to the model.
 */
qx.Class.define("gosa.data.controller.Workflow", {
  extend : gosa.data.controller.BaseObjectEdit,
  implement: [
    gosa.data.controller.IObject,
    gosa.data.controller.ITemplateDialogCreator
  ],

  /**
   * @param workflowObject {gosa.proxy.Object}
   */
  construct : function(workflowObject) {
    this.base(arguments);
    qx.core.Assert.assertInstance(workflowObject, gosa.proxy.Object);
    this.__workflowObject = workflowObject;

    this.__backendChangeController = new gosa.data.controller.BackendChanges(this.__workflowObject, this);

    this.__workflowObject.addListener(
      "foundDifferencesDuringReload",
      this.__backendChangeController.onFoundDifferenceDuringReload,
      this.__backendChangeController
    );

    this.__workflowObject.addListener("propertyUpdateOnServer", this.__onServerPropertyUpdated, this);

    this.__workflowObject.setUiBound(true);
  },

  members : {
    /**
     * @type {gosa.proxy.Object}
     */
    __workflowObject : null,
    __backendChangeController : null,
    __actionController : null,

    /**
     * @return {gosa.proxy.Object}
     */
    getObject : function() {
      return this.__workflowObject;
    },

    getObjectData: function() {
      var data = {};
      this.__workflowObject.attributes.forEach(function(attributeName) {
        var arr = this.__workflowObject.get(attributeName);
        if (arr instanceof qx.data.Array && arr.getLength() === 1) {
          data[attributeName] = arr.getItem(0);
        }
      }, this);
      return data;
    },

    addDialog : function(dialog) {
      if (qx.core.Environment.get("qx.debug")) {
        qx.core.Assert.assertInstance(dialog, qx.ui.window.Window);
        qx.core.Assert.assertNotNull(this._widget);
      }
      this._widget.addDialog(dialog);
    },

    /**
     * @param actionName {String}
     * @param context {gosa.engine.Context}
     */
    executeAction : function(actionName, context) {
      if (qx.core.Environment.get("qx.debug")) {
        qx.core.Assert.assertString(actionName);
        qx.core.Assert.assertInstance(context, gosa.engine.Context);
      }

      // create arguments for command
      var values = {};
      var widgetMap = context.getFreeWidgetRegistry().getMap();
      Object.getOwnPropertyNames(widgetMap).forEach(function(key) {
        var val = widgetMap[key].getValue();
        values[key] = gosa.ui.widgets.Widget.getSingleValue(val);
      });

      var args = this.__createArgumentsList(actionName + "()", context);
      args.push(qx.lang.Json.stringify(values));

      // execute command
      this.__workflowObject.callMethod.apply(this.__workflowObject, args)
        .then(function(result) {
          this.info(this, "Call of method '" + args[0] + "' was successful and returned '" + result + "'");
          // apply returned values to object
          var obj = context && !context.isDisposed() ? context.getObject() : this.__workflowObject;
          Object.getOwnPropertyNames(result).forEach(function(attr) {
            obj.set(attr, new qx.data.Array(result[attr]));
          }, this);
          return null;
        }, this)
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error).open();
        });
    },

    __createArgumentsList: function(target, context) {
      var parser = /^([^(]+)\((.*)\)$/;
      var parsed = parser.exec(target);
      var methodName = parsed[1];
      var params = parsed[2];
      var args = [];

      // create argument list
      if (qx.lang.Type.isString(params) && params !== "") {
        params = params.split(",");
        var paramParser = /%\(([^)]+)\)s/;
        var paramType = /\s*['"]([^'"]+)['"]\s*/;

        params.forEach(function(param) {
          var match = paramParser.exec(param);
          if (match) {
            throw new Error("Cannot use property '" + match[1] + "'")
            // var data = gosa.ui.widgets.Widget.getSingleValue(context.getActionController().getProperty(match[1]));
            // args.push(param.replace(match[0], data));
          } else {
            var typeMatch = paramType.exec(param);
            if (typeMatch) {
              args.push(typeMatch[1]);
            }
          }
        });
      }
      args.unshift(methodName);
      return args;
    },

    /**
      * @param widget {gosa.ui.widgets.WorkflowWizard}
      */
    setWidget : function(widget) {
      qx.core.Assert.assertInstance(widget, gosa.ui.widgets.WorkflowWizard);
      this._widget = widget;
    },

    /**
     * @return {gosa.ui.widgets.WorkflowWizard | null}
     */
    getWidget : function() {
      return this._widget;
    },

    /**
     * @return {Array | null} List of all attributes of the object
     */
    getAttributes : function() {
      return qx.lang.Type.isArray(this.__workflowObject.attributes) ? this.__workflowObject.attributes : null;
    },

    saveAndClose : function() {
      this.__workflowObject.commit().catch(gosa.ui.dialogs.Error.show, this).then(this.close, this);
    },

    close : function() {
      this.__workflowObject.setUiBound(false);
      this.__workflowObject.close();
      this._widget.fireEvent("close");
      this._widget.destroy();
      this.dispose();
    },

    // Interface methods
    closeWidgetAndObject : function() {
      this.close();
    },

    /**
     * @return {gosa.data.util.ExtensionFinder}
     */
    getExtensionFinder : function() {
      return null;
    },

    /**
     * @return {gosa.data.controller.Extensions}
     */
    getExtensionController : function() {
      return null;
    },

    /**
     * Calls the given method on the object.
     *
     * @param methodName {String} Name of the method
     * @return {qx.Promise}
     */
    callMethod : function(methodName) {
      qx.core.Assert.assertString(methodName);
      return this.__workflowObject.callMethod.apply(this.__workflowObject, arguments);
    },

    /**
     * @param ev {qx.event.type.Data}
     */
    __onServerPropertyUpdated : function(ev) {
      if (qx.core.Environment.get("qx.debug")) {
        qx.core.Assert.assertInstance(ev, qx.event.type.Data);
      }

      var data = ev.getData();
      var widget = this.getWidgetByAttributeName(data.property);

      if (widget) {
        widget.setValid(data.success);
        data.error && widget.setError(data.error.getData());

        this._widget.validate();
      }
    }
  },

  destruct : function() {
    this.__workflowObject.removeListener("propertyUpdateOnServer", this.__onServerPropertyUpdated, this);

    this.__workflowObject.removeListener(
      "foundDifferencesDuringReload",
      this.__backendChangeController.onFoundDifferenceDuringReload,
      this.__backendChangeController
    );

    this._disposeObjects(
      "__actionController",
      "__backendChangeController"
    );

    this.__workflowObject = null;
    this.__backendChangeController = null;
  }
});
