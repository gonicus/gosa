/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* ************************************************************************

#asset(gosa/*)

************************************************************************ */

qx.Class.define("gosa.view.Workflows",
{
  extend : qx.ui.tabview.Page,
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/app");
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.VBox(5));
    this._rpc = gosa.io.Rpc.getInstance();
    this._createChildControl("list");

    this.addListener("appear", this.__reload, this);
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    _listController : null,

    /**
     * Load the available Workflows and initialize the view
     * @private
     */
    __reload: function() {
      this._marshaler = new qx.data.marshal.Json();
      this._rpc.cA("getWorkflows").then(function(result) {
        var data = new qx.data.Array();
        for (var id in result) {
          var item = result[id];
          item.id = id;
          this._marshaler.toClass(item, true);
          data.push(this._marshaler.toModel(item, true));
        }
        this._listController.setModel(data);
      }, this)
      .catch(function(error) {
        this.error(error);
        new gosa.ui.dialogs.Error(error.message).open();
      });
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
        console.log(workflow);
        var doc = gosa.ui.window.Desktop.getInstance();
        win = new qx.ui.window.Window(this.tr("Workflow"));
        win.set({
          width        : 800,
          layout       : new qx.ui.layout.Canvas(),
          showMinimize : false,
          showClose    : false
        });
        win.add(widget, {edge : 0});
        gosa.data.WindowController.getInstance().addWindow(win, workflowItem);
        win.addListenerOnce("resize", function() {
          win.center();
          (new qx.util.DeferredCall(win.center, win)).schedule();
        }, this);
        win.open();

        widget.addListener("close", function() {
          gosa.data.WindowController.getInstance().removeWindow(win);
          controller.dispose();
          widget.dispose();
          doc.remove(win);
          win.destroy();
        });

        // Position window as requested
        doc.add(win);

        var controller = new gosa.data.ObjectEditController(workflow, widget);
        widget.setController(controller);
      }, this)
      .catch(this.error, this)
      .finally(function() {
        workflowItem.setLoading(false);
      });
    },

    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "list":
          control = new qx.ui.container.Composite(new gosa.ui.layout.Flow());
          this._listController = new gosa.data.controller.EnhancedList(null, control, "name");
          this._listController.setDelegate(this._getListDelegate());
          this.add(control, {flex: 1});
          break;
      }

      return control || this.base(arguments, id);
    },

    _getListDelegate: function() {
      return {
        createItem: function() {
          return new gosa.ui.form.WorkflowItem();
        },

        configureItem: function(item) {
          item.addListener("execute", function() {
            this.startWorkflow(item);
          }, this);
        }.bind(this),

        bindItem: function(controller, item , index) {
          controller.bindProperty("name", "label", null, item, index);
          controller.bindProperty("icon", "icon", {
            converter: function(value) {
              return value || "@Ligature/app"
            }
          }, item, index);
          controller.bindProperty("description", "description", null, item, index);
          controller.bindProperty("id", "id", null, item, index);
        },

        group: function(item) {
          return item.getCategory();
        }
      }
    }
  }
});
