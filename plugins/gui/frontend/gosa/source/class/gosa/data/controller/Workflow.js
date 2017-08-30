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
  implement: gosa.data.controller.IObject,

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

    this.__workflowObject.setUiBound(true);
  },

  members : {
    /**
     * @type {gosa.proxy.Object}
     */
    __workflowObject : null,
    __backendChangeController : null,

    /**
     * @return {gosa.proxy.Object}
     */
    getObject : function() {
      return this.__workflowObject;
    },

    /**
      * @param widget {gosa.ui.widgets.WorkflowWizard}
      */
    setWidget : function(widget) {
      qx.core.Assert.assertInstance(widget, gosa.ui.widgets.WorkflowWizard);
      this._widget = widget;
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
    }
  },

  destruct : function() {
    this.__workflowObject.removeListener(
      "foundDifferencesDuringReload",
      this.__backendChangeController.onFoundDifferenceDuringReload,
      this.__backendChangeController
    );

    this._disposeObjects(
      "__backendChangeController"
    );

    this.__workflowObject = null;
    this.__backendChangeController = null;
  }
});
