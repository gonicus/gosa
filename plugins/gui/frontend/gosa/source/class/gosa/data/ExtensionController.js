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

    this.__object = obj;
    this.__widgetController = widgetController;
    this.__extensionFinder = this.__widgetController.getExtensionFinder();
  },

  members : {
    __object : null,
    __widgetController : null,
    __extensionFinder : null,

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

    checkForMissingExtensions : function() {
      if (this.__extensionFinder.getAllMissingExtensionsAsArray().length) {
        var dialog = new gosa.ui.dialogs.AddDependentExtensions(this.__extensionFinder.getAllMissingExtensions());
        dialog.addListenerOnce("confirmed", this.__onMissingExtensionsDialogConfirm, this);
        dialog.open();
      }
    },

    /**
     * @param event {qx.event.type.Data}
     */
    __onMissingExtensionsDialogConfirm : function(event) {
      if (event.getData()) {
        this.__addMissingExtensions();
      }
      else {
        this.__retractExtensionsWithBrokenDependencies();
      }
    },

    __addMissingExtensions : function() {
      var sortedExtensions = this.__sortExtensions(this.__extensionFinder.getAllMissingExtensionsAsArray());
      this.__addExtensions(sortedExtensions);
    },

    __retractExtensionsWithBrokenDependencies : function() {
      var allExtensions = Object.keys(this.__extensionFinder.getAllMissingExtensions());
      var sortedExtensions = this.__sortExtensions(allExtensions).reverse();
      this.__retractExtensions(sortedExtensions);
    },

    /**
     * @param extensions {Array} Unique list of extension names
     */
    __addExtensions : function(extensions) {
      qx.core.Assert.assertArray(extensions);
      var queue = [];

      extensions.forEach(function(dependency) {
        queue.push(this._addExtensionToObject(dependency));
      }, this);
      qx.Promise.all(queue, this);
    },

    /**
     * @param extensions {Array} Unique list of extension names
     */
    __retractExtensions : function(extensions) {
      qx.core.Assert.assertArray(extensions);
      var queue = [];

      extensions.forEach(function(dependency) {
        queue.push(this._removeExtensionFromObject(dependency));
      }, this);
      qx.Promise.all(queue, this);
    },

    /**
     * Sorts the given extensions such that extending them in the final order will not cause dependency faults. Thus,
     * the list must be reversed for retraction.
     * @param extensions {Array}
     */
    __sortExtensions : function(extensions) {
      qx.core.Assert.assertArray(extensions);

      var ordered = this.__extensionFinder.getOrderedExtensions();
      extensions.sort(function(a, b) {
        return ordered.indexOf(a) - ordered.indexOf(b);
      });
      return extensions;
    },

    /**
     * Check dependencies of extension and possibly raise dialog which asks if to add other dependent extensions.
     *
     * @param extension {String}
     * @param modify {Boolean ? true} If the object shall be tagged as modified
     */
    _checkExtensionDependenciesExtend : function(extension, modify) {
      var dependencies = this.__extensionFinder.getMissingDependencies(extension);
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
      var activeExts = this.__widgetController.getActiveExtensions();

      // find dependencies
      var dependencies = [];
      var item;
      for (var ext in this.__object.extensionDeps) {
        if (this.__object.extensionDeps.hasOwnProperty(ext)) {
          item = this.__object.extensionDeps[ext];
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
        this.__addExtensions(dependencies.concat(extension));
      }, this);
    },

    _createRetractDependencyDialog : function(extension, dependencies) {
      var dialog = new gosa.ui.dialogs.RetractDependencies(extension, dependencies);
      dialog.show();

      dialog.addListenerOnce("ok", function() {
        this.__retractExtensions(dependencies.concat(extension));
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

      return this.__object.extend(extension)
      .then(function () {
        return qx.Promise.all([
          this.__object.refreshMetaInformation(),
          this.__object.refreshAttributeInformation()
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
        this.__widgetController.addExtensionTabs(templateObjects);
        if (modify) {
          this.__widgetController.setModified(true);
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

      return this.__object.retract(extension)
      .then(function() {
        return qx.Promise.all([
          this.__object.refreshMetaInformation(),
          this.__object.refreshAttributeInformation()
        ]);
      }, this)
      .then(function() {
        this.__widgetController.removeExtensionTab(extension);
        if (modify) {
          this.__widgetController.setModified(true);
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
    this.__object = null;
    this.__widgetController = null;
    this.__extensionFinder = null;
  }
});
