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
 * Controller for adding and removing extensions to/from an object.
 */
qx.Class.define("gosa.data.controller.Extensions", {

  extend : qx.core.Object,
  include : [qx.locale.MTranslation],

  /**
   * @param obj {gosa.proxy.Object}
   * @param widgetController {gosa.data.controller.ObjectEdit}
   */
  construct : function(obj, widgetController) {
    this.base(arguments);
    qx.core.Assert.assertInstance(obj, gosa.proxy.Object);
    qx.core.Assert.assertInstance(widgetController, gosa.data.controller.ObjectEdit);

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

      var dependencies = this.__extensionFinder.getExistingDependencies(extension);
      if (dependencies.length > 0) {
        this._createRetractDependencyDialog(extension, dependencies);
      }
      else {
        this.__removeExtensionFromObject(extension, modify);
      }
    },

    /**
     * Retracts the extension if it is in the object, its widgets are not initialized and there are no other extensions
     * on the object that need this extension.
     *
     * @param extensionName {String}
     * @return {Boolean} If the extension was retracted
     */
    retractIfNotAppearedAndIndependent : function(extensionName) {
      qx.core.Assert.assertString(extensionName);

      if (this.__extensionFinder.getExistingDependencies(extensionName).length === 0
        && this.__extensionFinder.isActiveExtension(extensionName)
        && !this.__isExtensionAppeared(extensionName)) {

        this.removeExtension(extensionName, false);
        return true;
      }
      return false;
    },

    /**
     * Adds the stated extension to the object.
     *
     * @param extension {String}
     */
    addExtension : function(extension) {
      qx.core.Assert.assertString(extension);

      var dependencies = this.__extensionFinder.getMissingDependencies(extension);
      if (dependencies.length > 0) {
        this._createExtendDependencyDialog(extension, dependencies);
      }
      else {
        this.__addExtensionToObject(extension, true);
      }
    },

    /**
     * Adds the given extension and its necessary dependencies without asking the user.
     *
     * @param extension {String}
     */
    addExtensionSilently : function(extension) {
      qx.core.Assert.assertString(extension);

      var dependencies = this.__extensionFinder.getMissingDependencies(extension);
      if (dependencies.length) {
        this.__addExtensions(this.__sortExtensions(dependencies).concat(extension));
      }
      else {
        this.__addExtensionToObject(extension, false);
      }
    },

    checkForMissingExtensions : function() {
      if (this.__extensionFinder.getAllMissingExtensionsAsArray().length) {
        var dialog = new gosa.ui.dialogs.AddDependentExtensions(this.__extensionFinder.getAllMissingExtensions());
        dialog.addListenerOnce("confirmed", this.__onMissingExtensionsDialogConfirm, this);
        dialog.open();
        this.__widgetController.addDialog(dialog);
      }
    },

    /**
     * Checks if an extension is not only present in the object, but also if the tab for it has appeared.
     *
     * @param extensionName {String}
     * @return {Boolean}
     */
    __isExtensionAppeared : function(extensionName) {
      var context = this.__widgetController.getContextByExtensionName(extensionName);
      return context && !context.isAppeared();
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
        queue.push(this.__addExtensionToObject(dependency));
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
        queue.push(this.__removeExtensionFromObject(dependency));
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

    _createExtendDependencyDialog : function(extension, dependencies) {
      var dialog = new gosa.ui.dialogs.ExtendDependencies(extension, dependencies);
      this.__widgetController.addDialog(dialog);
      dialog.show();

      dialog.addListenerOnce("ok", function() {
        this.__addExtensions(dependencies.concat(extension));
      }, this);
    },

    _createRetractDependencyDialog : function(extension, dependencies) {
      var dialog = new gosa.ui.dialogs.RetractDependencies(extension, dependencies);
      this.__widgetController.addDialog(dialog);
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
     * @return {qx.Promise}
     */
    __addExtensionToObject : function(extension, modify) {
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
    __removeExtensionFromObject : function(extension, modify) {
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
