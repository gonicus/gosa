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
 * Similar to {@link gosa.ui.widgets.TableWithSelector} but
 * opens a dialog instead of a selector. Another difference is that is shows the multiple values
 * from attributes defined by column names.
 */
qx.Class.define("gosa.ui.widgets.TableWithDialog", {
  extend: gosa.ui.widgets.TableWithSelector,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.base(arguments);

    this._errorRows = [];

    this.addListenerOnce("appear", function() {
      this._createGui();
      this._updatedTableData();
    }, this);
  },

  members: {
    _dialogTemplate: null,
    _additionalAttributes: null,

    // overridden
    _applyGuiProperties: function(props) {
      // This happens when this widgets gets destroyed - all properties will be set to null.
      if (props === null) {
        return;
      }
      this.base(arguments, props);

      if (props.hasOwnProperty("dialogTemplate")) {
        this._dialogTemplate = gosa.util.Template.compileTemplate(qx.lang.Json.stringify(props.dialogTemplate));
      }

      // check for additional attributes related to this dialog (we need to know those attributes to be able to delete the values)
      // so this guiProperty contains all attribute names which are not shown in the table but must be also deleted id a table
      // row gets removed
      if (props.hasOwnProperty("additionalAttributes")) {
        this._additionalAttributes = props.additionalAttributes;
      }
    },

    _createGui: function() {
      this._columnSettings.names.unshift("Index");
      this._columnSettings.ids.unshift("__identifier__");
      this.base(arguments);
      var tcm = this._table.getTableColumnModel();
      new qx.util.DeferredCall(function() {
        tcm.setColumnVisible(0, false);
      }).schedule();
      var object = this._getController().getObject();

      this._columnSettings.ids.forEach(function(attributeName, idx) {
        if (attributeName in object.attribute_data && object.attribute_data[attributeName].type === "Boolean") {
          tcm.setDataCellRenderer(idx, new qx.ui.table.cellrenderer.Boolean());
        }
      });
      this._table.removeListener("edit", this.openSelector, this);
      this._table.addListener("edit", function() {
        this._table.getSelectionModel().iterateSelection(function(row) {
          this.openSelector(this._tableModel.getRowData(row)['__identifier__']);
        }, this);
      }, this);
    },

    _updatedTableData: function(){
      this._updateDataModel();
    },

    _updateDataModel: function(){
      if (!this._table) {
        return;
      }
      this._tableData = [];
      var object = this._getController().getObject();
      this._columnSettings.ids.forEach(function(attributeName) {
        if (attributeName in object.attribute_data) {
          var arr = object.get(attributeName);
          arr.forEach(function(value, index) {
            if (this._tableData.length <= index) {
              this._tableData.push({});
            }
            this._tableData[index]["__identifier__"] = index;
            this._tableData[index][attributeName] = value;
          }, this);
        }
      }, this);
      this._tableModel.setDataAsMapArray(this._tableData, true, false);
      this._table.sort();
    },

    removeSelection : function(){
      // var value = this.getValue().toArray();
      var updated = false;

      this._table.getSelectionModel().iterateSelection(function(index) {
        var selected = this._tableModel.getRowData(index);
        var object = this._getController().getObject();
        if(selected){
          function removeValue(name) {
            if (name in object.attribute_data) {
              var value = object.get(name);
              value.removeAt(selected['__identifier__']);
              object.setAttribute(name, value);
            }
          }
          Object.getOwnPropertyNames(selected).forEach(removeValue, this);
          if (this._additionalAttributes) {
            this._additionalAttributes.forEach(removeValue, this);
          }
          updated = true;
        }
      }.bind(this));

      if (updated) {
        // this.setValue(new qx.data.Array(value));
        // this.fireDataEvent("changeValue", this.getValue().copy());
        this._table.getSelectionModel().resetSelection();
        this._updatedTableData();
      }
    },

    // overridden
    openSelector :  function(index) {
      if (index instanceof qx.event.type.Event) {
        // append new value
        index = this._tableData.length;
      }
      var controller = this._getController();
      var dialog = new gosa.ui.dialogs.TemplateDialog(this._dialogTemplate, controller, this.getExtension(), index);

      if (!(dialog instanceof qx.Promise)) {
        dialog = qx.Promise.resolve(dialog);
      }
      dialog.then(function(d) {
        d.open();
        if (controller) {
          controller.addDialog(d);
        }
        d.addListener("send", this._updatedTableData, this);
      }, this);


    }
  }
});
