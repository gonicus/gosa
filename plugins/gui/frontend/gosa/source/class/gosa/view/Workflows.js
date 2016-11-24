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

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@FontAwesome/f0c3");
    this.getChildControl("button").getChildControl("label").exclude();
    this.setLayout(new qx.ui.layout.VBox(5));
    this._rpc = gosa.io.Rpc.getInstance();

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
      this._rpc.cA("getWorkflows").then(function(result) {
        var data = new qx.data.Array();
        for (var id in result) {
          var item = result[id];
          item.id = id;
          data.push(item);
          this.__updateList(data);
        }
      }, this).catch(function(error) {
        new gosa.ui.dialogs.Error(error.message).open();
      });
    },

    __updateList: function(data) {
      var list = this.getChildControl("list");
      list.removeAll();
      data.forEach(function(dataItem) {
        var item = new gosa.ui.form.WorkflowItem();
        item.set({
          label: dataItem.name,
          icon: dataItem.icon || "@FontAwesome/f0c3",
          description: dataItem.description,
          id: dataItem.id
        });
        list.add(item);
        item.addListener("execute", function(ev) {
          this.startWorkflow(item);
        }, this);
      }, this);
    },

    startWorkflow: function(workflowItem) {
      var win = null;
      gosa.proxy.ObjectFactory.openWorkflow(function(workflow, error) {
        if (error) {
          this.error(error);
        } else {
          qx.Promise.all([
            workflow.get_templates(),
            workflow.get_translations(gosa.Config.getLocale())
          ]).spread(function(_templates, translations) {
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
            gosa.engine.WidgetFactory.createWorkflowWidget(function(w) {
              var doc = qx.core.Init.getApplication().getRoot();
              win = new qx.ui.window.Window(this.tr("Workflow"));
              win.set({
                width        : 800,
                layout       : new qx.ui.layout.Canvas(),
                showMinimize : false,
                showClose    : false
              });
              win.add(w, {edge : 0});
              win.addListenerOnce("resize", function() {
                win.center();
                (new qx.util.DeferredCall(win.center, win)).schedule();
              }, this);
              win.open();

              w.addListener("close", function() {
                controller.dispose();
                w.dispose();
                doc.remove(win);
                win.destroy();
              });

              // Position window as requested
              doc.add(win);

              var controller = new gosa.data.ObjectEditController(workflow, w);
              w.setController(controller);

              this.fireDataEvent("loadingComplete", {id : workflowItem.getId()});
            }, this, workflow, templates, translations);
          }, this).catch(this.error);
        }
      }, this, workflowItem.getId());
    },

    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "list":
          control = new qx.ui.container.Composite(new qx.ui.layout.Flow());
          this.add(control);
          break;
      }

      return control || this.base(arguments, id);
    }

  }
});
