/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.widgets.TableWithSelector", {

  extend: gosa.ui.widgets.Widget,

  construct: function(){

    this.base(arguments);
    this.contents.setLayout(new qx.ui.layout.Canvas());
    this.setDecorator("main");
    this._columnNames = [];
    this._tableData = [];
    this._resolvedNames = {};

    // Create the gui on demand
    this.addListener("initCompleteChanged", function(e){
      this._createGui();
      this._updatedTableData();
      this._errorRows = [];
    }, this);
  },

  destruct: function(){

    // Remove all listeners and then set our values to null.
    qx.event.Registration.removeAllListeners(this);

    this.setBuddyOf(null);
    this.setGuiProperties(null);
    this.setValues(null);
    this.setValue(null);
    this.setBlockedBy(null);

    this._disposeObjects("_table", "_actionBtn", "_widget", "_tableModel");

    this._tableData = null;
    this._columnNames = null;
    this._editTitle = null;
    this._columnIDs = null;
    this._firstColumn = null;
    this._resolvedNames = null;
    this._errorRows = null;
  },

  members: {

    _initially_set: false,
    _initially_send_update: true,

    _table: null,
    _tableModel: null,
    _tableData: null,
    _columnNames: null,
    _editTitle: "",
    _columnIDs: null,
    _firstColumn: null,
    _resolvedNames: null,
    _errorRows: null,

    /* Color the specific row red, if an error occurred!
     */
    setErrorMessage: function(message, id){
      this._table.colorRow('#F00', this._firstColumn, this._tableData[id][this._firstColumn]);
      this.setValid(false);
      this.setInvalidMessage(message);
    },

    /* Resets error messages
     * */
    resetErrorMessage: function(){
      this.setInvalidMessage("");
      this.setValid(true);
      this._table.resetRowColors();
    },

    _createGui: function(){
      this._tableModel = new qx.ui.table.model.Simple();
      this._tableModel.setColumns(this._columnNames, this._columnIDs);
      this._table = new gosa.ui.table.Table(this._tableModel);
      this._table.setStatusBarVisible(false);
      this._table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.MULTIPLE_INTERVAL_SELECTION);
      this.contents.add(this._table, {top:0 , bottom:0, right: 0, left:0});
      this._table.setPreferenceTableName(this.getExtension() + ":" + this.getAttribute());
      this.bind("valid", this._table, "valid");
      this.bind("invalidMessage", this._table, "invalidMessage");

      // Add new group membership
      this._table.addListener("dblclick", function(){

          var d = new gosa.ui.ItemSelector(this['tr'](this._editTitle), this.getValue().toArray(),
          this.getExtension(), this.getAttribute(), this._columnIDs, this._columnNames);

          d.addListener("selected", function(e){
              if(e.getData().length){
                this.setValue(this.getValue().concat(e.getData()));
                this.fireDataEvent("changeValue", this.getValue().copy());
              }
            }, this);

          d.open();

          //this.fireDataEvent("changeValue", new qx.data.Array(this.getValue().toArray()));
        }, this);

      // Add a remove listener
      this._table.addListener("remove", function(e){
        var that = this;
        var value = this.getValue().toArray();
        var updated = false;
        this._table.getSelectionModel().iterateSelection(function(index) {
            var selected = that._tableModel.getRowData(index);
            if(selected){
              updated = true;
              qx.lang.Array.remove(value, selected['__identifier__']);
            }
          });
        if(updated){
          this.setValue(new qx.data.Array(value));
          this.fireDataEvent("changeValue", this.getValue().copy());
        }
      }, this);
    },


    /* Update the table model and try to resolve missing values.
     * */
    _updatedTableData: function(data){
      this.__updateDataModel();
      this.__resolveMissingValues();
    },


    /* Applies a new value for this widget
     * */
    _applyValue: function(value){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(value === null){
        return;
      }

      // Add a listener to the content array.
      // On each modification update the table model.
      if(value){
        value.addListener("change", function(){
          this._updatedTableData();
        },this);
      }
      this._updatedTableData();

      // Send initial content to process validators"
      if(this._initially_set && this._initially_send_update){
        var data = value.copy();
        data.setUserData("initial", true);
        this.fireDataEvent("changeValue", data);
        this._initially_send_update = false;
      }
      this._initially_set = true;

    },


    /* Resolve missing value information
     * */
    __resolveMissingValues: function(){

      var rpc = gosa.io.Rpc.getInstance();
      var values = this.getValue().toArray();

      var unknown_values = [];
      for(var i=0; i<values.length; i++){
        if(!(values[i] in this._resolvedNames)){
          unknown_values.push(values[i]);

          var row_data = {};
          row_data[this._firstColumn] = values[i];
          row_data["__identifier__"] = values[i];
          this._resolvedNames[values[i]] = row_data;
        }
      }

      if(unknown_values.length){
        rpc.cA(function(result, error){
          if(error){
            new gosa.ui.dialogs.Error(error.message).open();
            return;
          }else{
            for(var value in result['map']){
              var data = result['result'][result['map'][value]];
              if(data){
                data['__identifier__'] = value;
                this._resolvedNames[value] = data;
              }
            }
            this.__updateDataModel();
          }
        }, this, "getObjectDetails", this.getExtension(), this.getAttribute(), unknown_values, this._columnIDs);
      }else{
        this.__updateDataModel();
      }
    },


    /* Set the visible content of the table.
     * */
    __updateDataModel: function(){
      if(!this._table){
        return;
      }
      this._tableData = [];
      var values = this.getValue().toArray();
      for(var i=0; i<values.length; i++ ){
        var row_data = {};
        if(values[i] in this._resolvedNames){
          row_data = this._resolvedNames[values[i]];
        }else{
          row_data[this._firstColumn] = values[i];
        }
        this._tableData.push(row_data);
      }
      this._tableModel.setDataAsMapArray(this._tableData, true, false);
      this._table.sort();
    },


    /* Apply porperties that were defined in the ui-tempalte.
     *
     * Collect column names here.
     * */
    _applyGuiProperties: function(props){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(props === null){
        return;
      }

      if('editTitle' in props){
        this._editTitle = props['editTitle'];
      }
      this._columnNames = [];
      this._columnIDs = [];
      var first = null;
      if('columns' in props){
        for(var col in props['columns']){
          this._columnNames.push(this['tr'](props['columns'][col]));
          this._columnIDs.push(col);
          if(!first){
            first = col;
          }
        }
      }
      this._firstColumn = first;
    }
  }
});
