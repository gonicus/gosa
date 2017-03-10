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
 * Shows an overview of the current values of some {@link #attributes} of an object.
 */
qx.Class.define("gosa.ui.widgets.ValuesOverview", {

  extend: qx.ui.core.Widget,

  construct : function() {
    this.base(arguments);

    var layout = new qx.ui.layout.Grid();
    layout.setColumnFlex(0, 1);
    layout.setColumnFlex(1, 1);
    this._setLayout(layout);
  },

  properties: {

    /**
     * An array consisting of maps with the keys "label" and "value".
     */
    labelsAndValues : {
      check : "Array",
      apply : "_applyLabelsAndValues"
    }
  },

  members : {

    _applyLabelsAndValues : function(value) {
      this._removeAll().forEach(function(widget) {
        if (!widget.isDisposed()) {
          widget.dispose();
        }
      });

      var row = 0;
      value.forEach(function(config) {
        // check value
        if (!(config.value instanceof qx.data.Array)) {
          qx.log.Logger.error("Value must be a qx.data.Array (label='" + config.label + "')");
          return;
        }
        var value = new qx.ui.basic.Label(this.__stringify(config.value));
        var label = new qx.ui.basic.Label(config.label);

        this._add(label, {
          row : row,
          column : 0
        });
        this._add(value, {
          row : row,
          column : 1
        });
        row++;
      }, this);
    },

    __stringify : function(value) {
      switch (value.getLength()) {
        case 0:
          return "";

        case 1:
          return value.getItem(0);

        default:
          var l = Math.min(3, value.getLength());
          var s = value.slice(0, l).join(", ");
          if (value.getLength() > l) {
            s += "...";
          }
          return s;
      }
    }
  }
});
