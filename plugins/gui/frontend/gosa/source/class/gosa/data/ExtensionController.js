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
     * Removes the extension from the object in that its tab page(s) won't be shown any more.
     *
     * @param extension {String} Name of the extension (e.g. "SambaUser")
     */
    removeExtension : function(extension) {
      qx.core.Assert.assertString(extension);
      this._checkExtensionDependenciesRetract(extension);
    },

    /**
     * Adds the stated extension to the object.
     *
     * @param extension {String}
     */
    addExtension : function(extension) {
      qx.core.Assert.assertString(extension);
      this._checkExtensionDependenciesExtend(extension);
    },

    /**
     * Check dependencies of extension and possibly raise dailog which asks if to add other dependent extensions.
     */
    _checkExtensionDependenciesExtend : function(extension) {
      var dependencies = this._obj.extensionDeps[extension] ? qx.lang.Array.clone(this._obj.extensionDeps[extension]) : [];

      dependencies = dependencies.filter(function(ext) {
        return !this._obj.extensionTypes[ext];
      }, this);

      if (dependencies.length > 0) {
        this._createExtendDependencyDialog(extension, dependencies);
      }
      else {
        this._addExtensionToObject(extension);
      }
    },

    /**
     * Check dependencies of extension and possibly raise dailog which asks if to remove the other extensions.
     */
    _checkExtensionDependenciesRetract : function(extension) {
      var activeExts = this._widgetController.getActiveExtensions();

      // find dependencies
      var dependencies = [];
      var item;
      for (var ext in this._obj.extensionDeps) {
        if (this._obj.extensionDeps.hasOwnProperty(ext)) {
          item = this._obj.extensionDeps[ext];
          if (qx.lang.Array.contains(item, extension) && item && qx.lang.Array.contains(activeExts, ext) &&
            gosa.Cache.gui_templates[ext] && gosa.Cache.gui_templates[ext].length > 0) {
            dependencies.push(ext);
          }
        }
      }

      if (dependencies.length > 0) {
        this._createRetractDependencyDialog(extension, dependencies);
      }
      else {
        this._removeExtensionFromObject(extension);
      }
    },

    _createExtendDependencyDialog : function(extension, dependencies) {
      var dialog = new gosa.ui.dialogs.ExtendDependencies(extension, dependencies);
      dialog.show();

      dialog.addListenerOnce("ok", function() {
        var queue = [];

        dependencies.forEach(function(dependency) {
          queue.push([this._addExtensionToObject, this, [dependency]]);
        }, this);

        queue.push([this._addExtensionToObject, this, [extension]]);
        gosa.Tools.serialize(queue);
      }, this);
    },

    _createRetractDependencyDialog : function(extension, dependencies) {
      var dialog = new gosa.ui.dialogs.RetractDependencies(extension, dependencies);
      dialog.show();

      dialog.addListenerOnce("ok", function() {
        var queue = [];

        dependencies.forEach(function(dependency) {
          queue.push([this._removeExtensionFromObject, this, [dependency]]);
        }, this);

        queue.push([this._removeExtensionFromObject, this, [extension]]);
        gosa.Tools.serialize(queue);
      }, this);
    },

    _addExtensionToObject : function(extension, callback) {
      qx.core.Assert.assertString(extension);

      this._obj.extend(function (result, error) {
        if (error) {
          new gosa.ui.dialogs.Error(
            qx.lang.String.format(this.tr("Failed to extend the %1 extension: %2"), [extension, error.message])).open();
          this.error(error.message);
        }
        else {
          this._obj.refreshMetaInformation(function() {});
          this._obj.refreshAttributeInformation(function () {
            this._widgetController.addExtensionTabs(gosa.util.Template.getTemplateObjects(extension, this._obj.baseType));
            this._widgetController.setModified(true);

            if (callback) {
              qx.core.Assert.assertFunction(callback);
              callback();
            }
          }, this);
        }
      }, this, extension);
    },

    /**
     * Removes (aka disables) the extension from the object. Dependent extensions will also be removed.
     *
     * @param extension {String} Name of the extension, e.g. "UserSamba"
     * @param callback {Function ? null} Optional callback to invoke once the extension has been retracted
     */
    _removeExtensionFromObject : function(extension, callback) {
      qx.core.Assert.assertString(extension);

      this._obj.retract(function(result, error) {
        if (error) {
          new gosa.ui.dialogs.Error(
            qx.lang.String.format(this.tr("Failed to retract the %1 extension: %2"),
            [extension, error.message])
          ).open();
          this.error(error.message);
        }
        else {
          this._widgetController.removeExtensionTab(extension);
          this._widgetController.setModified(true);
        }
        this._obj.refreshMetaInformation(function() {});

        if (callback) {
          qx.core.Assert.assertFunction(callback);
          callback();
        }
      }, this, extension);
    }
  },

  destruct : function() {
    this._obj = null;
    this._widgetController = null;
  }
});
