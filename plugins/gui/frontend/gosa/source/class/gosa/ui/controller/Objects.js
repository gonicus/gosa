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
* This controller handles all object/workflow open/close operations
*/
qx.Class.define("gosa.ui.controller.Objects", {
  extend : qx.core.Object,
  type: "singleton",
  
  construct : function() {
    this.base(arguments);

    this._desktop = new qx.ui.window.Desktop();
    this._windowController = gosa.data.controller.Window.getInstance();

    this.__root = qx.core.Init.getApplication().getRoot();
    this.__root.addListener("resize", this._onRootResize, this);
    this._onRootResize();
    this.__openObjects = {};
  },
    
  members : {
    _desktop: null,
    _windowController: null,
    __windowWidth : null,
    __root: null,
    __openObjects: null,

    _onRootResize: function() {
      var rootBounds = this.__root.getBounds();
      var newWidth = Math.max(850, Math.round(rootBounds.width/1.5));
      if (newWidth !== this.__windowWidth) {
        this._windowController.getWindows().forEach(function(tuple) {
          var window = tuple.getItem(0);
          if (!window.isMaximized()) {
            window.setWidth(newWidth);
          }
        }, this);
      }
      this.__windowWidth = newWidth;
    },

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
        this.__openObjects[dn] = obj;
        // Build widget and place it into a window
        return qx.Promise.all([
          obj,
          gosa.engine.WidgetFactory.createWidget(obj)
        ]);
      }, this)
      .spread(function(obj, w) {
        win = new qx.ui.window.Window(qx.locale.Manager.tr("Object") + ": " + obj.dn);
        obj.addListener("moved", function(ev) {
          win.setCaption(ev.getData());
        }, this);
        var bounds = this._desktop.getBounds();
        win.set({
          width : this.__windowWidth,
          layout : new qx.ui.layout.Canvas(),
          showMinimize : true,
          showClose : false,
          maxHeight: bounds.height,
          allowGrowY: true
        });

        if (bounds.width < 1024 || bounds.height < 720) {
          win.maximize();
        }

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
          delete this.__openObjects[dn];
        }, this);

        w.addListener("timeoutClose", function() {
          this._windowController.removeWindow(win);
        }, this);

        // Position window as requested
        this._desktop.add(win);

        var controller = new gosa.data.controller.ObjectEdit(obj, w);
        w.setController(controller);
        return w;
      }, this)
      .catch(function(error) {
        this.error(error);
        new gosa.ui.dialogs.Error(error).open();
      }, this);
    },

    startWorkflow: function(workflowItem, reference_object_dn) {
      workflowItem.setLoading(true);
      var win = null;
      gosa.proxy.ObjectFactory.openWorkflow(workflowItem.getId(), reference_object_dn)
      .then(function(workflow) {
        this.__openObjects[workflowItem.getId()] = workflow;
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
            localeManager.addTranslation(gosa.Config.getLocale(), translations[name]);
          }
          if (_templates.hasOwnProperty(name)) {
            templates.push({
              index     : parseInt(_templates[name]['index']),
              extension : name,
              template  : gosa.util.Template.compileTemplate(_templates[name]['content'])
            });
          }
        }
        templates.sort(function(a, b) {
          return a.index - b.index;
        });

        return qx.Promise.all([workflow, templates]);
      }, this)
      .spread(function(workflow, templates) {
        win = new qx.ui.window.Window(qx.locale.Manager.tr("Workflow") + " - " + workflowItem.getLabel());
        var bounds = this._desktop.getBounds();
        win.set({
          width        : this.__windowWidth,
          layout       : new qx.ui.layout.Canvas(),
          showMinimize : false,
          showClose    : false,
          maxHeight    : bounds.height,
          allowGrowY   : true
        });

        var widget = gosa.engine.WidgetFactory.createWorkflowWidget(workflow, templates);

        win.add(widget, {edge : 0});
        this._windowController.addWindow(win, workflowItem);
        win.addListenerOnce("resize", function() {
          (new qx.util.DeferredCall(win.center, win)).schedule();
        }, this);
        win.open();

        widget.addListener("close", function() {
          this._windowController.removeWindow(win);
          this._desktop.remove(win);
          win.destroy();
          delete this.__openObjects[workflowItem.getId()];
        }, this);

        // Position window as requested
        this._desktop.add(win);
      }, this)
      .catch(this.error, this)
      .finally(function() {
        workflowItem.setLoading(false);
      });
    },

    /**
     * Close all opened objects
     * @return {qx.Promise}
     */
    closeAllObjects: function() {
      var promises = [];
      for (var id in this.__openObjects) {
        if (this.__openObjects.hasOwnProperty(id)) {
          promises.push(this.__openObjects[id].close());
        }
      }
      return qx.Promise.all(promises);
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
    this.__root.removeListener("resize", this._onRootResize, this);
    this.__root = null;
  }
});
