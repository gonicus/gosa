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

/**
 * The tree folder is a tree element, which can have nested tree elements.
 */
qx.Class.define("gosa.ui.tree.Application", {
  extend: qx.ui.tree.TreeFile,
  include: gosa.ui.widgets.MDragDrop,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(label) {
    this._initialLabel = label;
    this.base(arguments, label);
    this._parameters = {};
    this._initialParameterValues = {};
    this._initDrapDropListeners();
    this._applyDragDropGuiProperties({
      dragDropType: "gosa/menuEntry",
      draggable: true
    });
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "changedValue": "qx.event.type.Data"
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    name: {
      check: "String",
      nullable: true,
      apply: "_applyName"
    },

    cn: {
      check: "String",
      nullable: true
    },

    gosaApplicationName: {
      check: "String",
      nullable: true
    },

    modified: {
      check: "Boolean",
      init: false,
      event: "changeModified"
    },

    draggable: {
      refine: true,
      init: true
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    _parameters: null,
    _initialParameterValues: null,

    _onDropRequest: function(ev) {
      var action = ev.getCurrentAction();
      var type = ev.getCurrentType();

      if (type === this.getDragDropType()) {

        if (action === "move") {
          this.getParent().remove(this)
        }

        ev.addData(this.getDragDropType(), this);
      }
    },

    _applyName: function(value) {
      this.setLabel(value);
    },

    _applyLabel: function(value, old) {
      this.base(arguments, value, old);
      this.setModified(this._initialLabel !== value);
      if (this._initialLabel !== undefined) {
        this.fireDataEvent("changedValue", value);
      }
    },

    /**
     * Initialie parameter and save value as initial
     * @param key {String}
     * @param initialValue {String}
     */
    initParameter: function(key, initialValue) {
      this._initialParameterValues[key] = initialValue;
      if (!this._parameters.hasOwnProperty(key)) {
        this._parameters[key] = initialValue;
      }
    },

    /**
     * Set parameter value (create if it does not exist yet)
     * @param key {String}
     * @param value {String}
     */
    setParameter: function(key, value) {
      var changed = this._parameters.hasOwnProperty(key) && this._parameters[key] !== value;
      this._parameters[key] = value;
      if (changed) {
        this.fireDataEvent("changedValue", value);
      }
      this._checkModification();
    },

    getParameterValue: function(key) {
      return this._parameters.hasOwnProperty(key) ? this._parameters[key] : "";
    },

    _checkModification: function() {
      var modified = false;
      Object.getOwnPropertyNames(this._parameters).some(function(key) {
        if (this._parameters[key] && this._parameters[key] !== this._initialParameterValues[key]) {
          modified = true;
          return true;
        }
      }, this);
      this.setModified(modified);
    },

    toJson: function() {
      var parameters = [];
      Object.getOwnPropertyNames(this._parameters).forEach(function(key) {
        if (this._parameters[key] && this._parameters[key] !== this._initialParameterValues[key]) {
          parameters.push(key+":"+this._parameters[key]);
        }
      }, this);

      return {
        name: this.getLabel(),
        cn: this.getCn(),
        gosaApplicationParameter: parameters
      }
    }
  }
});
