/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* This controller handles all object/workflow open/close operations
*/
qx.Class.define("gosa.ui.controller.Objects", {
  extend : qx.core.Object,
  type: "singleton",
  
  construct : function() {
    this.base(arguments);

    this._desktop = new qx.ui.window.Desktop();
    this._windowController = gosa.data.WindowController.getInstance();
  },
    
  properties : {
    
  },
    
  members : {
    _desktop: null,
    _windowController: null,

    getDesktop: function() {
      return this._desktop;
    },

    /**
     * Open the object given by its uuid/dn
     */
    openObject : function(dn, type) {
      var win = null;
      return gosa.proxy.ObjectFactory.openObject(dn, type)
      .then(function(obj) {
        // Build widget and place it into a window
        return qx.Promise.all([
          obj,
          gosa.engine.WidgetFactory.createWidget(obj)
        ]);
      }, this)
      .spread(function(obj, w) {
        win = new qx.ui.window.Window(qx.locale.Manager.tr("Object") + ": " + obj.dn);
        var bounds = this._desktop.getBounds();
        win.set({
          width : 800,
          layout : new qx.ui.layout.Canvas(),
          showMinimize : true,
          showClose : false,
          maxHeight: bounds.height - 10,
          allowGrowY: true
        });
        win.add(w, {edge: 0});
        this._windowController.addWindow(win, obj);
        win.addListenerOnce("resize", function(ev) {
          (new qx.util.DeferredCall(win.center, win)).schedule();
        }, this);
        win.open();

        w.addListener("close", function() {
          this._windowController.removeWindow(win);
          controller.dispose();
          w.dispose();
          this._desktop.remove(win);
          win.destroy();
        }, this);

        w.addListener("timeoutClose", function() {
          this._windowController.removeWindow(win);
        }, this);

        // Position window as requested
        this._desktop.add(win);

        var controller = new gosa.data.ObjectEditController(obj, w);
        w.setController(controller);
      }, this)
      .catch(function(error) {
        this.error(error);
        new gosa.ui.dialogs.Error(error).open();
      }, this);
    },

    startWorkflow: function(workflowItem) {
      workflowItem.setLoading(true);
      var win = null;
      gosa.proxy.ObjectFactory.openWorkflow(workflowItem.getId())
      .then(function(workflow) {
        return qx.Promise.all([
          workflow,
          workflow.get_templates(),
          workflow.get_translations(gosa.Config.getLocale())
        ]);
      }, this)
      .spread(function(workflow, _templates, translations) {
        var templates = new qx.data.Array(_templates.length);

        var localeManager = qx.locale.Manager.getInstance();
        for (var name in _templates) {
          if (translations.hasOwnProperty(name)) {
            // add translations to make them available before the template gets compiled
            localeManager.addTranslation(gosa.Config.getLocale(), qx.lang.Json.parse(translations[name]));
          }
          if (_templates.hasOwnProperty(name)) {
            templates.insertAt(parseInt(_templates[name]['index']), {
              extension : name,
              template  : gosa.util.Template.compileTemplate(_templates[name]['content'])
            });
          }
        }

        // Build widget and place it into a window
        return qx.Promise.all([
          workflow,
          gosa.engine.WidgetFactory.createWorkflowWidget(workflow, templates, translations)
        ]);
      }, this)
      .spread(function(workflow, widget) {
        win = new qx.ui.window.Window(qx.locale.Manager.tr("Workflow"));
        var bounds = this._desktop.getBounds();
        win.set({
          width        : 800,
          layout       : new qx.ui.layout.Canvas(),
          showMinimize : false,
          showClose    : false,
          maxHeight: bounds.height - 10,
          allowGrowY: true
        });
        win.add(widget, {edge : 0});
        this._windowController.addWindow(win, workflowItem);
        win.addListenerOnce("resize", function() {
          (new qx.util.DeferredCall(win.center, win)).schedule();
        }, this);
        win.open();

        widget.addListener("close", function() {
          this._windowController.removeWindow(win);
          controller.dispose();
          widget.dispose();
          this._desktop.remove(win);
          win.destroy();
        }, this);

        // Position window as requested
        this._desktop.add(win);

        var controller = new gosa.data.ObjectEditController(workflow, widget);
        widget.setController(controller);
      }, this)
      .catch(this.error, this)
      .finally(function() {
        workflowItem.setLoading(false);
      });
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._desktop = null;
    this._windowController = null;
  }
});