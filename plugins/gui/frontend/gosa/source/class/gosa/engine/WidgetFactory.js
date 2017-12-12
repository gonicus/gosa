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

qx.Class.define("gosa.engine.WidgetFactory", {
  type : "static",

  statics : {

    /**
     * Create a new widget for the given object and invoke the callback afterwards.
     *
     * @param obj {gosa.proxy.Object} The objects.* object for which the widget shall be created
     */
    createWidget : function(obj) {
      qx.core.Assert.assertInstance(obj, gosa.proxy.Object);

      return new qx.Promise(function(resolve, reject) {
        // collect templates
        var templates = [];
        var addTemplates = function(name) {
          qx.lang.Array.append(templates, gosa.util.Template.getTemplateObjects(name));
        };

        addTemplates(obj.baseType);

        // extensions
        if ("extensionTypes" in obj) {
          var extensions = obj.extensionTypes;
          for (var ext in extensions) {
            if (extensions.hasOwnProperty(ext) && extensions[ext]) {
              addTemplates(ext);
            }
          }
        }

        // generate widget
        var widget = new gosa.ui.widgets.ObjectEdit(templates);

        resolve(widget);
      }, this);
    },

    /**
     * Create a new widget for the given workflow.
     *
     * @param workflow {gosa.proxy.Object} The workflows.* workflow for which the widget shall be created
     * @param templates {qx.data.Array} array of templates for the workflow
     */
    createWorkflowWidget : function(workflow, templates) {
      qx.core.Assert.assertInstance(workflow, gosa.proxy.Object);
      qx.core.Assert.assertInstance(templates, qx.data.Array);

      var controller = new gosa.data.controller.Workflow(workflow);
      var widget = new gosa.ui.widgets.WorkflowWizard(workflow, controller, templates);
      controller.setWidget(widget);
      return widget;
    },

    /**
     * Tries to find and create the dialog from the given name. It is first searched for a corresponding class under
     * {@link gosa.ui.dialogs}. If that is not found, it looks into the transferred cache of dialog templates.
     *
     * @param name {String} Name of the dialog class/template
     * @param controller {gosa.data.controller.ITemplateDialogCreator ? null} Optional object controller
     * @param extension {String} Name of the extension that the dialog is created in
     * @return {gosa.ui.dialogs.Dialog | null} The (unopened) dialog widget
     */
    createDialog : function(name, controller, extension) {
      qx.core.Assert.assertString(name);
      qx.core.Assert.assertString(extension);
      if (controller) {
        qx.core.Assert.assertQxObject(controller);
        qx.core.Assert.assertInterface(controller, gosa.data.controller.ITemplateDialogCreator);
      }

      var dialog = null;
      if (name.startsWith("RPC:")) {
        return gosa.io.Rpc.getInstance().cA(name.substring(4), controller ? controller.getObjectData() : null)
        .then(function(template) {
          var templateString = qx.lang.Json.stringify(template);
          var compiledTemplate = gosa.util.Template.compileTemplate(templateString);
          return qx.Promise.resolve(new gosa.ui.dialogs.TemplateDialog(compiledTemplate, controller, extension));
        });
      } else {
        var splitted = name.split(".");

        // Make class name start with an uppercase letter
        var clazzName = splitted[splitted.length - 1];
        clazzName = clazzName.substring(0, 1).toUpperCase() + clazzName.substring(1);
        splitted[splitted.length - 1] = clazzName;
        var clazz = qx.Class.getByName("gosa.ui.dialogs." + splitted.join("."));

        // directly known class
        if (clazz) {
          dialog = new clazz(controller);
          dialog.setAutoDispose(true);
        }
        else {
          // find dialog template
          var template = gosa.data.TemplateRegistry.getInstance().getDialogTemplate(name);
          if (template) {
            dialog = new gosa.ui.dialogs.TemplateDialog(template, controller, extension);
          }
        }
      }

      if (controller) {
        controller.addDialog(dialog);
      }
      return dialog;
    }
  }
});
