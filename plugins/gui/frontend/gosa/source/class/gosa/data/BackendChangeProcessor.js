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
qx.Class.define("gosa.data.BackendChangeProcessor", {

  extend : qx.core.Object,

  /**
   * @param object {gosa.proxy.Object}
   * @param controller {gosa.data.ObjectEditController}
   */
  construct : function(object, controller) {
    this.base(arguments);

    qx.core.Assert.assertInstance(object, gosa.proxy.Object);
    qx.core.Assert.assertInstance(controller, gosa.data.ObjectEditController);
    this.__obj = object;
    this.__controller = controller;
    this.__modifiedValues = {};
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
      this.__widgetConfigurations = [];
      this.__processChanges(event.getData().attributes.changed);
      this.__processRemoved(event.getData().attributes.removed);
      this.__processAdded(event.getData().attributes.added);

      if (this.__widgetConfigurations.length > 0) {
        this.__createMergeDialog(this.__widgetConfigurations);
      }
      this.__widgetConfigurations = null;
    },

    /**
     * @param changes {Map} Hash map with changes to the model (key is attribute name, value is the new value)
     */
    __processChanges : function(changes) {
      qx.core.Assert.assertMap(changes);

      var widget, newVal;
      for (var attributeName in changes) {
        if (changes.hasOwnProperty(attributeName)) {
          newVal = new qx.data.Array(qx.lang.Type.isArray(changes[attributeName]) ? changes[attributeName] : [changes[attributeName]]);
          widget = this.__controller.getWidgetByAttributeName(attributeName);

          if (widget) {
            this.__modifiedValues[attributeName] = newVal;
            var mergeWidgets = this.__getMergeWidgetConfiguration(widget, attributeName, newVal);
            this.__widgetConfigurations.push(mergeWidgets);
          }
          else {
            this.__obj.set(attributeName, newVal);
          }
        }
      }
    },

    /**
     * @param Added {Map} Hash map with new attribute values to the model (key is attribute name, value is the new value)
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
            this.__obj.set(attributeName, newVal);
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
          this.__obj.set(attributeName, newVal);
        }
      }, this);
    },

    /**
     * @param mergeConfiguration {Array}
     */
    __createMergeDialog : function(mergeConfiguration) {
      qx.core.Assert.assertArray(mergeConfiguration);

      if (this.__mergeDialog) {
        this.__mergeDialog.close();
      }

      var dialog = this.__mergeDialog = new gosa.ui.dialogs.MergeDialog(mergeConfiguration);
      dialog.addListenerOnce("merge", this.__onMerge, this);
      dialog.open();
      dialog.center();
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
      var attributes = event.getData().attributes;

      for (var attributeName in attributes) {
        if (attributes.hasOwnProperty(attributeName)) {
          if (!attributes[attributeName]) {  // change value to remote one
            var widget = this.__controller.getWidgetByAttributeName(attributeName);
            widget.setValue(this.__modifiedValues[attributeName]);
          }
          else {
            this.__controller.setModified(true);
          }
          this.__modifiedValues[attributeName] = null;
        }
      }

      this.__mergeDialog = null;
    }
  },

  destruct : function() {
    this.__obj = null;
    this.__controller = null;
    this.__modifiedValues = null;
    this.__widgetConfigurations = null;
    this.__mergeDialog = null;
  }
});
