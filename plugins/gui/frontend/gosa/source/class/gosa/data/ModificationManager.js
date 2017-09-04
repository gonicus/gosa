/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */
/**
 * This class keeps track of the modification state of attribute values, i.e. it saves the original value of an
 * attribute and compares it to the current value, deciding whether it is modified.
 */
qx.Class.define("gosa.data.ModificationManager", {

  extend : qx.core.Object,

  /**
   * @param model {gosa.proxy.Object}
   */
  construct : function(object) {
    this.base(arguments);
    qx.core.Assert.assertInstance(object, gosa.proxy.Object);
    this.__object = object;
    this.__watchedAttributes = {};
  },

  properties : {

    /**
     * READ-ONLY
     *
     * If the object (i.e. one of the registered attributes) is modified.
     */
    modified : {
      check : "Boolean",
      init : false,
      event : "changeModified"
    }
  },

  members : {

    /**
     * @type {gosa.proxy.Object}
     */
    __object : null,

    /**
     * @type {Object} Map of attribute name -> copy of original value
     */
    __watchedAttributes : null,

    /**
     * Add an attribute that shall be observed.
     *
     * @param attributeName {String}
     */
    registerAttribute : function(attributeName) {
      if (this.__watchedAttributes.hasOwnProperty(attributeName)) {
        this.warn("Attribute '" + attributeName + "' is already being watched. Ignoring.");
        return;
      }

      this.__watchedAttributes[attributeName] = this.__object.get(attributeName).copy();

      this.__object.addListener(qx.Class.getPropertyDefinition(
        this.__object.constructor, attributeName).event,
        this.__changedValue,
        this);

      if (this.__object.get(attributeName) instanceof qx.data.Array) {
        this.__object.get(attributeName).addListener("change", this.__updateModified, this);
      }
      this.__updateModified();
    },

    /**
     * Sometimes Objects receive changes from backend which should not be treated as
     * changes (silent merge). This method updates the comparison value in those cases
     * @param attributeName {String}
     */
    updateAttribute : function(attributeName) {
      if (!this.__watchedAttributes.hasOwnProperty(attributeName)) {
        this.warn("Attribute '" + attributeName + "' is not being watched. Ignoring.");
        return;
      }
      this.__watchedAttributes[attributeName] = this.__object.get(attributeName).copy();

      this.__updateModified();
    },

    /**
     * Remove an attribute from observation.
     *
     * @param attributeName {String}
     */
    unregisterAttribute : function(attributeName) {
      if (!this.__watchedAttributes.hasOwnProperty(attributeName)) {
        this.warn("Attribute '" + attributeName + "' is not being watched. Ignoring.");
        return;
      }

      this.__object.removeListener(qx.Class.getPropertyDefinition(
        this.__object.constructor, attributeName).event,
        this.__changedValue,
        this);

      if (this.__object.get(attributeName) instanceof qx.data.Array) {
        this.__object.get(attributeName).removeListener("change", this.__updateModified, this);
      }

      this.__watchedAttributes[attributeName].dispose();
      delete this.__watchedAttributes[attributeName];

      this.__updateModified();
    },

    /**
     * Stop observing all attributes. This is automatically called on dispose.
     */
    unregisterAllAttributes : function() {
      Object.keys(this.__watchedAttributes).forEach(this.unregisterAttribute, this);
    },

    __updateModified : function() {
      if (this.isDisposed()) {
        return;
      }
      var attr, current, i;
      for (var attributeName in this.__watchedAttributes) {
        if (this.__watchedAttributes.hasOwnProperty(attributeName)) {
          attr = this.__watchedAttributes[attributeName];
          current = this.__object.get(attributeName);

          if (attr.getLength() !== current.getLength() && !current.every(function(v) { return v === "" || v === null || v === undefined; })) {
            this.setModified(true);
            return;
          }

          for (i = 0; i < attr.getLength(); i++) {
            if (attr.getItem(i) !== current.getItem(i)) {
              this.setModified(true);
              return;
            }
          }
        }
      }
      this.setModified(false);
    },

    /**
     * @param event {qx.event.type.Data}
     */
    __changedValue : function(event) {
      if (event.getOldData() instanceof qx.data.Array) {
        event.getOldData().removeListener("change", this.__updateModified, this);
      }
      if (event.getData() instanceof qx.data.Array) {
        event.getData().addListener("change", this.__updateModified, this);
      }
      this.__updateModified();
    }
  },

  destruct : function() {
    if (!this.__object.isDisposed()) {
      this.unregisterAllAttributes();
    }
    this.__object = null;
    this.__watchedAttributes = null;
  }
});