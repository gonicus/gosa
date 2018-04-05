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

qx.Class.define("gosa.ui.widgets.TableWithSelector", {

  extend: gosa.ui.widgets.Widget,

  include: [
    gosa.ui.widgets.MDragDrop,
    gosa.ui.table.MColumnSettings
  ],

  construct: function(valueIndex){

    this.base(arguments, valueIndex);
    this.contents.setLayout(new qx.ui.layout.Canvas());
    this.setDecorator("main");
    this._columnSettings = {names: [], ids: [], renderers: [], widths: []};
    this._tableData = [];
    this._resolvedNames = {};
    this._selectorOptions = {};
    this.__listeners = [];

    // Create the gui on demand
    this.addListener("initCompleteChanged", function(e){
      if (e.getData()) {
        this._createGui();
        this._updatedTableData();
        this._errorRows = [];
      }
    }, this);
  },

  properties : {
    hasSelection : {
      init : false,
      event : "changeHasSelection"
    }
  },

  members: {

    _initially_set: false,
    _initially_send_update: true,

    _table: null,
    _tableModel: null,
    _tableData: null,
    _columnSettings: null,
    _editTitle: "",
    _firstColumn: null,
    _resolvedNames: null,
    _errorRows: null,
    _sortByColumn: null,
    _initiallyHiddenColumns: null,
    _modelFilter: null,
    _selectorOptions: null,
    _contextMenuConfig: null,
    __listeners: null,

    /* Color the specific row red, if an error occurred!
     */
    setErrorMessage: function(message, id){
      if (id) {
        this._table.colorRow('#F00', this._firstColumn, this._tableData[id][this._firstColumn]);
      }
      this.setValid(false);
      this.setInvalidMessage(message);
    },

    /**
     * Resets error messages
     */
    resetErrorMessage: function(){
      this.setInvalidMessage("");
      this.setValid(true);
      this._table.resetRowColors();
    },

    _createGui: function(){
      this._tableModel = new qx.ui.table.model.Simple();
      this._tableModel.setColumns(this._columnSettings.names, this._columnSettings.ids);
      if (this._sortByColumn) {
        this._tableModel.sortByColumn(this._tableModel.getColumnIndexById(this._sortByColumn), true);
      }
      this._table = new gosa.ui.table.Table(this._tableModel);
      if (this._contextMenuConfig) {
        for (var i = 0, l = this._columnSettings.ids.length; i < l; i++) {
          this._table.setContextMenuHandler(i, this._contextMenuHandlerRow, this);
        }
        if (this._contextMenuConfig.hasOwnProperty("marker")) {
          // listen to object property changes
          var object = this._getController().getObject();
          var property = qx.util.PropertyUtil.getProperties(object.constructor)[this._contextMenuConfig.marker.ref];
          this.__listeners.push([object, object.addListener(property.event, this._onMarkerPropertyChange, this)]);
        }
      }
      this._table.setStatusBarVisible(false);
      this._table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.MULTIPLE_INTERVAL_SELECTION);
      this._table.getSelectionModel().addListener("changeSelection", function() {
        this.setHasSelection(!!this._table.getSelectionModel().getSelectedCount());
      }, this);
      this.contents.add(this._table, {top:0 , bottom:0, right: 0, left:0});
      this._table.setPreferenceTableName(this.getExtension() + ":" + this.getAttribute());
      this.bind("valid", this._table, "valid");
      this.bind("invalidMessage", this._table, "invalidMessage");

      // Listeners
      this._table.addListener("edit", this.openSelector, this);
      this._table.addListener("remove", this.removeSelection, this);
      this._applyColumnSettings(this._table, this._columnSettings);

      // drag&drop
      this._initDragDropListeners();

      // check if we have some table filters
      var object = this._getController().getObject();

      if (this.getAttribute() && object.attribute_data[this.getAttribute()]["validator_information"]) {
        Object.getOwnPropertyNames(object.attribute_data[this.getAttribute()]["validator_information"]).forEach(function(info) {
          var settings = object.attribute_data[this.getAttribute()]["validator_information"][info];
          if (info === "MaxAllowedTypes") {
            var filter = new gosa.data.filter.AllowedValues();
            if (settings.hasOwnProperty("key")) {
              filter.setPropertyName(settings.key);
            }
            if (settings.hasOwnProperty("maximum")) {
              filter.setMaximum(settings.maximum);
            }
            this._modelFilter = filter;
          }
        }, this);
      }
    },

    _onDropRequest: function(e) {
      var action = e.getCurrentAction();
      var type = e.getCurrentType();

      if (type === this.getDragDropType()) {

        var selection = [];
        this._table.getSelectionModel().iterateSelection(function(row) {
          var data = this._tableModel.getRowData(row);
          selection.push(data["__identifier__"]);
        }.bind(this));

        if (action === "move") {
          this.removeSelection();
        }

        e.addData(this.getDragDropType(), selection);
      }
    },

    openSelector :  function() {
      var d = new gosa.ui.dialogs.ItemSelector(
        this['tr'](this._editTitle),
        this.getValue().toArray(),
        this.getExtension(),
        this.getAttribute(),
        this._columnSettings,
        false,
        this._modelFilter,
        this._sortByColumn,
        null,
        this._selectorOptions);

      d.addListener("selected", function(e){
        if(e.getData().length){
          this.setValue(this.getValue().concat(e.getData()));
          this.fireDataEvent("changeValue", this.getValue().copy());
        }
      }, this);

      this._getController().addDialog(d);
      d.open();
    },

    removeSelection : function(){
      var value = this.getValue().toArray();
      var updated = false;

      this._table.getSelectionModel().iterateSelection(function(index) {
        var selected = this._tableModel.getRowData(index);
        if(selected){
          updated = true;
          qx.lang.Array.remove(value, selected['__identifier__']);
        }
      }.bind(this));

      if (updated) {
        this.setValue(new qx.data.Array(value));
        this.fireDataEvent("changeValue", this.getValue().copy());
        this._table.getSelectionModel().resetSelection();
      }
    },

    _updatedTableData: function(){
      this.__updateDataModel();
      this.__resolveMissingValues();
    },

    _applyValue: function(value){
      if (value === null) {
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


    /**
     * Resolve missing value information
     */
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
        rpc.cA("getObjectDetails", this.getExtension(), this.getAttribute(), unknown_values, this._columnSettings.ids)
        .then(function(result) {
          for(var value in result['map']){
            var data = result['result'][result['map'][value]];
            if(data){
              data['__identifier__'] = value;
              this._resolvedNames[value] = data;
            }
          }
          this.__updateDataModel();
        }, this)
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error).open();
        });
      }else{
        this.__updateDataModel();
      }
    },

    __updateDataModel: function(){
      if (!this._table) {
        return;
      }
      this._tableData = [];

      this.getValue().toArray().forEach(function(value) {
        var row_data = {};
        if (value in this._resolvedNames) {
          row_data = this._resolvedNames[value];
        }
        else {
          row_data[this._firstColumn] = value;
        }
        this._tableData.push(row_data);
      }, this);

      if (this._modelFilter) {
        this._modelFilter.warmup(this._tableData);
      }
      this._tableModel.setDataAsMapArray(this._tableData, true, false);
      this._table.sort();

      this._onMarkerPropertyChange();
    },

    _contextMenuHandlerRow: function(col, row, table, dataModel, contextMenu) {
      if (!this._contextMenuConfig) {
        return;
      }
      var showMenu = false;
      Object.getOwnPropertyNames(this._contextMenuConfig).forEach(function(type) {
        var button;
        switch (type) {
          case "marker":
            var conf = this._contextMenuConfig.marker;
            button = new qx.ui.menu.Button(conf.title);
            var refColumn = dataModel.getColumnIndexById(conf.columnId);
            var currentValue = dataModel.getValue(refColumn, row);
            var normalizedValue = this.__normalizeMarkerValue(currentValue);
            var marked = normalizedValue !== currentValue;

            var object = this._getController().getObject();
            button.addListener("execute", function() {
              if (marked) {
                // unmark
                object.set(conf.ref, new qx.data.Array());
              } else {
                // mark
                object.set(conf.ref, new qx.data.Array([normalizedValue]));

              }
            }, this);
            break;

          default:
            this.warn("unhandled menu entry type: ", type);
            break;
        }
        if (button) {
          contextMenu.add(button);
          showMenu = true;
        }
      }, this);
      return showMenu;
    },

    __normalizeMarkerValue: function(currentValue) {
      var conf = this._contextMenuConfig.marker;
      var normalizedValue = currentValue;
      if (conf.hasOwnProperty("suffix") && currentValue.endsWith(conf.suffix)) {
        normalizedValue = currentValue.substring(0, currentValue.length - conf.suffix.length);
      }
      if (conf.hasOwnProperty("prefix") && currentValue.startsWith(conf.prefix)) {
        normalizedValue = normalizedValue.substring(conf.prefix.length);
      }
      return normalizedValue;
    },

    __markValue: function(value) {
      var conf = this._contextMenuConfig.marker;
      var newValue = value;
      if (conf.suffix) {
        newValue += conf.suffix;
      }
      if (conf.prefix) {
        newValue = conf.prefix + newValue;
      }
      return newValue;
    },

    _onMarkerPropertyChange: function(ev) {
      if (this._contextMenuConfig && this._contextMenuConfig.marker) {
        var conf = this._contextMenuConfig.marker;
        var object = this._getController().getObject();
        var value = gosa.ui.widgets.Widget.getSingleValue(object.get(conf.ref));
        var refColumn = this._tableModel.getColumnIndexById(conf.columnId);
        var data = this._tableModel.getData();
        for (var row = 0, l = data.length; row < l; row++) {
          var cellValue = data[row][refColumn];
          var normalized = this.__normalizeMarkerValue(cellValue);
          if (normalized === value) {
            // mark this one
            this._tableModel.setValue(refColumn, row, this.__markValue(normalized));
          } else {
            this._tableModel.setValue(refColumn, row, normalized);
          }
        }
      }
    },

    _applyGuiProperties: function(props){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(props === null){
        return;
      }

      if('editTitle' in props){
        this._editTitle = props['editTitle'];
      }

      this._applyDragDropGuiProperties(props);

      this._columnSettings = {
        names: [],
        ids: [],
        renderers: {},
        widths: {}
      };
      var first = null;
      if('columns' in props){
        for(var col in props['columns']){
          if (props['columns'].hasOwnProperty(col)) {
            this._columnSettings.names.push(this['tr'](props['columns'][col]));
            this._columnSettings.ids.push(col);
            if (!first) {
              first = col;
            }
          }
        }
      }
      if (props.hasOwnProperty("columnRenderers")) {
        this._columnSettings.renderers = props.columnRenderers;
      }
      if (props.hasOwnProperty("columnWidths")) {
        this._columnSettings.widths = props.columnWidths;
      }
      this._firstColumn = first;
      if ("sortByColumn" in props) {
        this._sortByColumn = props.sortByColumn;
      }
      if (props.hasOwnProperty("contextMenu")) {
        this._contextMenuConfig = props.contextMenu;
      }
      if (props.hasOwnProperty("selectorOptions")) {
        this._selectorOptions = props.selectorOptions;
      }
    }
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
    this._columnSettings = null;
    this._editTitle = null;
    this._firstColumn = null;
    this._resolvedNames = null;
    this._errorRows = null;
    this._selectorOptions = null;
    this.__listeners.forEach(function(entry) {
      entry[0].removeListenerById(entry[1]);
    });
    this.__listeners = [];
  }
});
