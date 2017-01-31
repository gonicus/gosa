/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Processes backend changes of an object.
 */
qx.Class.define("gosa.data.controller.BackendChanges", {

  extend : qx.core.Object,

  /**
   * @param object {gosa.proxy.Object}
   * @param controller {gosa.data.controller.ObjectEdit}
   */
  construct : function(object, controller) {
    this.base(arguments);

    qx.core.Assert.assertInstance(object, gosa.proxy.Object);
    qx.core.Assert.assertInstance(controller, gosa.data.controller.ObjectEdit);
    this.__obj = object;
    this.__controller = controller;
    this.__modifiedValues = {};

    this.__obj.addListener("closing", this.__onObjectClosing, this);
   },

  members : {
    __obj : null,
    __controller : null,
    __modifiedValues : null,
    __widgetConfigurations : null,
    __mergeDialog : null,

    /**
     * @param event {qx.event.type.Data}
     */
    onFoundDifferenceDuringReload : function(event) {
      var data = event.getData();
      this.__widgetConfigurations = [];

      this.__processChanges(data.attributes.changed);
      this.__processRemoved(data.attributes.removed);
      this.__processAdded(data.attributes.added);
      this.__processExtensions(data.extensions);

      if (data.extensions.removed.length > 0) {
        // differences cannot be merged
        this.__createUnableToMergeDialog();
        this.__controller.closeWidgetAndObject();
      }
      else if (this.__widgetConfigurations.length > 0 || this.__hasExtensions(data)) {
        this.__createMergeDialog(
          this.__widgetConfigurations,
          data.attributes.blocked_by,
          data.extensions
        );
      }
      this.__widgetConfigurations = null;
    },

    /**
     * @param attributeName {String}
     * @param value {var}
     */
    __setAttributeValue : function(attributeName, value) {
      qx.core.Assert.assertString(attributeName);

      this.__obj.setWriteAttributeUpdates(false);
      this.__obj.set(attributeName, value);
      this.__obj.setWriteAttributeUpdates(true);
    },

    /**
     * @param data {Object}
     */
    __hasExtensions : function(data) {
      return data.extensions.removed.length > 0;
    },

    /**
     * @param data {Object}
     */
    __processExtensions : function(data) {
      qx.core.Assert.assertMap(data);

      this.__processAddedExtensions(data.add);
      this.__processRetractedExtensions(data.removed);
    },

    /**
     * @param addedExtensions {Array}
     */
    __processAddedExtensions: function(addedExtensions) {
      if (qx.lang.Type.isArray(addedExtensions)) {
        addedExtensions.forEach(this.__addExtensionIfMissing, this);
      }
    },

    /**
     * @param extension {String}
     */
    __addExtensionIfMissing : function(extension) {
      qx.core.Assert.assertString(extension);
      if (!this.__controller.getExtensionFinder().isActiveExtension(extension)) {
        this.__controller.getExtensionController().addExtensionSilently(extension);
      }
    },

    /**
     * @param retractedExtensions {Array}
     */
    __processRetractedExtensions : function(retractedExtensions) {
      if (!qx.lang.Type.isArray(retractedExtensions)) {
        return;
      }
      var removed = [];
      retractedExtensions.forEach(function(extensionName) {
        var isRemoved = this.__controller.getExtensionController().retractIfNotAppearedAndIndependent(extensionName);
        if (isRemoved) {
          removed.push(extensionName);
        }
      }, this);
      qx.lang.Array.exclude(retractedExtensions, removed);
    },

    /**
     * @param changes {Map} Hash map with changes to the model (key is attribute name, value is the new value)
     */
    __processChanges : function(changes) {
      qx.core.Assert.assertMap(changes);

      var widget, newVal;
      for (var attributeName in changes) {
        if (changes.hasOwnProperty(attributeName)) {
          newVal = new qx.data.Array(
            qx.lang.Type.isArray(changes[attributeName])
            ? changes[attributeName]
            : [changes[attributeName]]);
          widget = this.__controller.getWidgetByAttributeName(attributeName);

          if (widget) {
            this.__modifiedValues[attributeName] = newVal;
            var mergeWidgets = this.__getMergeWidgetConfiguration(widget, attributeName, newVal);
            this.__widgetConfigurations.push(mergeWidgets);
          }
          else {
            this.__setAttributeValue(attributeName, newVal);
          }
        }
      }
    },

    /**
     * @param added {Map} Hash map with new attribute values to the model (key is attribute name, value is the new value)
     */
    __processAdded : function(added) {
      qx.core.Assert.assertMap(added);

      var widget, newVal;
      for (var attributeName in added) {
        if (added.hasOwnProperty(attributeName)) {
          newVal = new qx.data.Array(qx.lang.Type.isArray(added[attributeName]) ? added[attributeName] : [added[attributeName]]);
          widget = this.__controller.getWidgetByAttributeName(attributeName);

          if (widget) {
            this.__modifiedValues[attributeName] = newVal;
            var mergeWidgets = this.__getMergeWidgetConfiguration(widget, attributeName, newVal);
            this.__widgetConfigurations.push(mergeWidgets);
          }
          else {
            this.__setAttributeValue(attributeName, newVal);
          }
        }
      }
    },

    /**
     * @param removed {Array} List of names of the attributes that are removed
     */
    __processRemoved : function(removed) {
      qx.core.Assert.assertArray(removed);
      removed.forEach(function(attributeName) {
        var widget = this.__controller.getWidgetByAttributeName(attributeName);
        var newVal = new qx.data.Array();

        if (widget) {
          this.__modifiedValues[attributeName] = newVal;
          var mergeWidgets = this.__getMergeWidgetConfiguration(widget, attributeName, newVal);
          this.__widgetConfigurations.push(mergeWidgets);
        }
        else {
          this.__setAttributeValue(attributeName, newVal);
        }
      }, this);
    },

    /**
     * @param mergeConfiguration {Array}
     * @param block {Object}
     * @param extensionsData {Object}
     */
    __createMergeDialog : function(mergeConfiguration, block, extensionsData) {
      qx.core.Assert.assertArray(mergeConfiguration);
      qx.core.Assert.assertObject(block);

      if (this.__mergeDialog) {
        this.__mergeDialog.close();
      }

      var dialog = this.__mergeDialog = new gosa.ui.dialogs.MergeDialog(
        mergeConfiguration,
        extensionsData,
        block,
        this.__obj.extensionDeps,
        this.__controller.getExtensionFinder().getOrderedExtensions()
      );
      dialog.addListenerOnce("merge", this.__onMerge, this);
      dialog.open();
      dialog.center();
    },

    __createUnableToMergeDialog : function() {
      var msg = qx.locale.Manager.tr("While you were modifying the object, it has been updated in a manner which makes it impossible to merge the changes. Therefore, the object has been closed. Sorry.");
      var dialog = new gosa.ui.dialogs.Info(msg);
      dialog.setAutoDispose(true);
      dialog.open();
    },

    /**
     * Creates an array with the corresponding merge widgets.
     *
     * @param widget {gosa.ui.widget.Widget} Existing widget for the attribute
     * @param attributeName {String}
     * @param remoteValue {qx.data.Array} The value that shall be merged with the current one
     * @return {Object} Hash maps with the keys 'localWidget', 'remoteWidget', 'label', 'attributeName'
     */
    __getMergeWidgetConfiguration : function(widget, attributeName, remoteValue) {
      qx.core.Assert.assertInstance(widget, gosa.ui.widgets.Widget);
      qx.core.Assert.assertString(attributeName);
      qx.core.Assert.assertInstance(remoteValue, qx.data.Array);

      var widgetClass = widget.constructor;
      var buddy = this.__controller.getBuddyByAttributeName(attributeName);

      var localWidget;
      var localValue = widget.getValue();
      if (localValue.getLength() === 0 || localValue.getItem(0) === "") {
        localWidget = new qx.ui.basic.Label("<i>" + qx.locale.Manager.tr("removed") + "<i>");
        localWidget.setRich(true);
      }
      else {
        localWidget = widgetClass.getMergeWidget(widget.getValue())
      }

      var remoteWidget;
      if (remoteValue.getLength() === 0) {
        remoteWidget = new qx.ui.basic.Label("<i>" + qx.locale.Manager.tr("removed") + "<i>");
        remoteWidget.setRich(true);
      }
      else {
        remoteWidget = widgetClass.getMergeWidget(remoteValue);
      }

      return {
        attributeName : attributeName,
        localWidget : localWidget ,
        remoteWidget : remoteWidget,
        label : buddy ? buddy.getValue().getItem(0) : null
      };
    },

    /**
     * @param event {qx.event.type.Data}
     */
    __onMerge : function(event) {
      var data = event.getData();

      this.__mergeAttributes(data.attributes);
      this.__mergeExtensions(data.ext);

      this.__mergeDialog = null;
    },

    __mergeAttributes : function(attributes) {
      var val;
      for (var attributeName in attributes) {
        if (attributes.hasOwnProperty(attributeName)) {
          if (!attributes[attributeName]) {  // change value to remote one
            var widget = this.__controller.getWidgetByAttributeName(attributeName);
            val = this.__modifiedValues[attributeName];
            if (val instanceof qx.data.Array && val.getLength() === 0) {
              widget.getValue().removeAll();
            }
            else {
              widget.setValue(val);
            }
          }
          else {
            this.__controller.setModified(true);
          }
          this.__modifiedValues[attributeName] = null;
        }
      }
    },

    /**
     * @param extensions {Object}
     */
    __mergeExtensions : function(extensions) {
      qx.core.Assert.assertMap(extensions);
      var activeExtensions = this.__controller.getActiveExtensions();

      for (var ext in extensions) {
        if (extensions.hasOwnProperty(ext)) {
          this.__handleExtension(ext, extensions[ext], activeExtensions);
        }
      }
    },

    /**
     * @param extension {String} Name of the extension
     * @param takeLocal {Boolean} If the local state shall be used
     * @param activeExtensions {Array} Names of currently active extensions
     */
    __handleExtension : function(extension, takeLocal, activeExtensions) {
      qx.core.Assert.assertString(extension);
      qx.core.Assert.assertBoolean(takeLocal);
      qx.core.Assert.assertArray(activeExtensions);

      if (takeLocal) {
        this.__controller.getExtensionController().addExtensionSilently(extension);
      }
      else if (!takeLocal && qx.lang.Array.contains(activeExtensions, extension)) {
        this.__controller.getExtensionController().removeExtension(extension, false);
      }
    },

    /**
     * @param event {qx.event.type.Data}
     */
    __onObjectClosing : function(event) {
      if (event.getData().state === "closed" && this.__mergeDialog) {
        this.__mergeDialog.close();
        this.__mergeDialog = null;
      }
    }
  },

  destruct : function() {
    if (this.__obj && !this.__obj.isDisposed()) {
      this.__obj.removeListener("closing", this.__onObjectClosing, this);
    }
    this.__obj = null;
    this.__controller = null;
    this.__modifiedValues = null;
    this.__widgetConfigurations = null;
    this.__mergeDialog = null;
  }
});
