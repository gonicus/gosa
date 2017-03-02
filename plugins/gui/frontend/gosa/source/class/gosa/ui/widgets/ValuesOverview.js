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
        if (config.value.getLength() > 1) {
          qx.log.Logger.error("Value for label '" + config.label + "' must have length <= 1, but is " +
            config.value.getLength());
          return;
        }

        var value = new qx.ui.basic.Label(config.value.getLength() === 1 ? config.value.getItem(0) : "");
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
    }
  }
});
