/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Controller for adding and removing extensions to/from an object.
 */
qx.Class.define("gosa.data.ExtensionController", {

  extend : qx.core.Object,
  include : [qx.locale.MTranslation],

  /**
   * @param obj {gosa.proxy.Object}
   * @param widgetController {gosa.data.ObjectEditController}
   */
  construct : function(obj, widgetController) {
    this.base(arguments);
    qx.core.Assert.assertInstance(obj, gosa.proxy.Object);
    qx.core.Assert.assertInstance(widgetController, gosa.data.ObjectEditController);

    this._obj = obj;
    this._widgetController = widgetController;
  },

  members : {
    _obj : null,
    _widgetController : null,

    /**
     * Returns all extensions of the object in an order that prevents dependency faults.
     *
     * @return {Array} List of extension names (Strings); might be empty
     */
    getOrderedExtensions : function() {
      var result = [];
      var deps = this._obj.extensionDeps;

      var resolveDep = function(name) {
        var currentDeps = deps[name];
        if (currentDeps.length > 0) {
          for (var ext in currentDeps) {
            if (currentDeps.hasOwnProperty(ext)) {
              resolveDep(currentDeps[ext]);
            }
          }
        }
        if (!qx.lang.Array.contains(result, name)) {
          result.push(name);
        }
      };

      for (var ext in deps) {
        if (deps.hasOwnProperty(ext)) {
          resolveDep(ext);
        }
      }

      return result;
    },

    /**
     * Returns a list of extensions that the object can be extended by.
     *
     * @return {Array} List of extension names (as strings); might be empty
     */
    getExtendableExtensions : function() {
      var result = [];
      var exts = this._obj.extensionTypes;

      for (var ext in exts) {
        if (exts.hasOwnProperty(ext) && !exts[ext]) {
          result.push(ext);
        }
      }
      return result;
    },

    /**
     * Returns a list of extensions that can be retracted from the object.
     *
     * @return {Array} List of extension names (as strings); might be empty
     */
    getRetractableExtensions : function() {
      var result = [];
      var exts = this._obj.extensionTypes;

      for (var ext in exts) {
        if (exts.hasOwnProperty(ext) && exts[ext]) {
          result.push(ext);
        }
      }
      return result;
    },

    /**
     * Removes the extension from the object in that its tab page(s) won't be shown any more.
     *
     * @param extension {String} Name of the extension (e.g. "SambaUser")
     * @param modify {Boolean ? true} If the object shall be tagged as modified
     */
    removeExtension : function(extension, modify) {
      qx.core.Assert.assertString(extension);
      this._checkExtensionDependenciesRetract(extension, modify);
    },

    /**
     * Adds the stated extension to the object.
     *
     * @param extension {String}
     * @param modify {Boolean ? true} If the object shall be tagged as modified
     */
    addExtension : function(extension, modify) {
      qx.core.Assert.assertString(extension);
      this._checkExtensionDependenciesExtend(extension, modify);
    },

    /**
     * Check dependencies of extension and possibly raise dialog which asks if to add other dependent extensions.
     *
     * @param extension {String}
     * @param modify {Boolean ? true} If the object shall be tagged as modified
     */
    _checkExtensionDependenciesExtend : function(extension, modify) {
      var dependencies = this._obj.extensionDeps[extension] ? qx.lang.Array.clone(this._obj.extensionDeps[extension]) : [];

      dependencies = dependencies.filter(function(ext) {
        return !this._obj.extensionTypes[ext];
      }, this);

      if (dependencies.length > 0) {
        this._createExtendDependencyDialog(extension, dependencies);
      }
      else {
        this._addExtensionToObject(extension, modify);
      }
    },

    /**
     * Check dependencies of extension and possibly raise dailog which asks if to remove the other extensions.
     *
     * @param extension {String}
     * @param modify {Boolean ? true} If the object shall be tagged as modified
     */
    _checkExtensionDependenciesRetract : function(extension, modify) {
      var activeExts = this._widgetController.getActiveExtensions();

      // find dependencies
      var dependencies = [];
      var item;
      for (var ext in this._obj.extensionDeps) {
        if (this._obj.extensionDeps.hasOwnProperty(ext)) {
          item = this._obj.extensionDeps[ext];
          if (qx.lang.Array.contains(item, extension) && item && qx.lang.Array.contains(activeExts, ext) &&
            gosa.data.TemplateRegistry.getInstance().hasTemplate(ext)) {
            dependencies.push(ext);
          }
        }
      }

      if (dependencies.length > 0) {
        this._createRetractDependencyDialog(extension, dependencies);
      }
      else {
        this._removeExtensionFromObject(extension, modify);
      }
    },

    _createExtendDependencyDialog : function(extension, dependencies) {
      var dialog = new gosa.ui.dialogs.ExtendDependencies(extension, dependencies);
      dialog.show();

      dialog.addListenerOnce("ok", function() {
        var queue = [];

        dependencies.forEach(function(dependency) {
          queue.push(this._addExtensionToObject(dependency));
        }, this);

        queue.push(this._addExtensionToObject(extension));
        return qx.Promise.all(queue, this);
      }, this);
    },

    _createRetractDependencyDialog : function(extension, dependencies) {
      var dialog = new gosa.ui.dialogs.RetractDependencies(extension, dependencies);
      dialog.show();

      dialog.addListenerOnce("ok", function() {
        var queue = [];

        dependencies.forEach(function(dependency) {
          queue.push(this._removeExtensionFromObject(dependency));
        }, this);

        queue.push(this._removeExtensionFromObject(extension));
        return qx.Promise.all(queue, this);
      }, this);
    },

    /**
     * Adds (aka enables) the extension to the object.
     *
     * @param extension {String} Name of the extension, e.g. "UserSamba"
     * @param modify {Boolean ? true} If the object shall be tagged as modified
     * @returns {qx.Promise}
     */
    _addExtensionToObject : function(extension, modify) {
      if (modify !== false) {
        modify = true;
      }
      qx.core.Assert.assertString(extension);

      return this._obj.extend(extension)
      .then(function () {
        return qx.Promise.all([
          this._obj.refreshMetaInformation(),
          this._obj.refreshAttributeInformation()
        ]);
      }, this)
      .then(function() {
        var templateObjects = [];
        gosa.data.TemplateRegistry.getInstance().getTemplates(extension).forEach(function(template) {
          templateObjects.push({
            extension: extension,
            template: template
          })
        });
        this._widgetController.addExtensionTabs(templateObjects);
        if (modify) {
          this._widgetController.setModified(true);
        }
      }, this)
      .catch(function(error) {
        new gosa.ui.dialogs.Error(
        qx.lang.String.format(this.tr("Failed to extend the %1 extension: %2"), [extension, error.getData().message])).open();
        this.error(error);
      }, this);
    },

    /**
     * Removes (aka disables) the extension from the object. Dependent extensions will also be removed.
     *
     * @param extension {String} Name of the extension, e.g. "UserSamba"
     * @param modify {Boolean ? true} If the object shall be tagged as modified
     * @return {qx.Promise}
     */
    _removeExtensionFromObject : function(extension, modify) {
      if (modify !== false) {
        modify = true;
      }
      qx.core.Assert.assertString(extension);

      return this._obj.retract(extension)
      .then(function() {
        return qx.Promise.all([
          this._obj.refreshMetaInformation(),
          this._obj.refreshAttributeInformation()
        ]);
      }, this)
      .then(function() {
        this._widgetController.removeExtensionTab(extension);
        if (modify) {
          this._widgetController.setModified(true);
        }
      }, this)
      .catch(function(error) {
        new gosa.ui.dialogs.Error(
        qx.lang.String.format(this.tr("Failed to retract the %1 extension: %2"),
        [extension, error.getData().message])
        ).open();
        this.error(error);
      }, this);
    }
  },

  destruct : function() {
    this._obj = null;
    this._widgetController = null;
  }
});
