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

/*
#asset(gosa/*)
*/

qx.Class.define("gosa.ui.dialogs.ItemSelector", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function(title, current_values, extension, attribute, column_keys, column_names, single, modelFilter, sortByColumn, mode, options) {
    this.base(arguments);
    this.setCaption(title);
    this.setResizable(true, true, true, true);
    this.setWidth(500);
    this.setLayout(new qx.ui.layout.VBox(0));
    this._sortByColumn = sortByColumn;

    this.__isSingleSelection = !!single;

    this.__initWidgets(column_names, column_keys, extension, attribute);

    this._detailsRpc = mode || "searchForObjectDetails";

    options = options || {};
    var queryFilter =  "";
    if (options.hasOwnProperty('queryFilter')) {
      queryFilter = options.queryFilter;
    } else {
      options.limit = 100;
    }
    if (modelFilter) {
      options.filter = modelFilter.getSearchOptions();
    }

    this._searchArgs = {
      extension: extension,
      attribute: attribute,
      queryFilter: queryFilter,
      columnKeys: column_keys,
      currentValues: current_values,
      options: options,
      modelFilter: modelFilter
    };

    if (!options.skipInitialSearch) {
      this._updateValues();
    }
  },

  events: {
    "selected": "qx.event.type.Data"
  },

  members : {
    __table : null,
    __tableModel : null,
    _tableContainer: null,
    __isSingleSelection : false,
    _sortByColumn: null,
    _detailsRpc: null,
    _throbber: null,
    _filter: null,


    _updateValues: function(queryFilter) {
      if (!queryFilter) {
        queryFilter = this._searchArgs.queryFilter
      }
      if (!this._throbber) {
        this._throbber = new gosa.ui.Throbber();
        this._throbber.addState("blocking");
        this._tableContainer.add(this._throbber, {edge: 0});
      } else {
        this._throbber.show();
      }
      gosa.io.Rpc.getInstance().cA(
        this._detailsRpc,
        this._searchArgs.extension,
        this._searchArgs.attribute,
        queryFilter,
        this._searchArgs.columnKeys,
        this._searchArgs.currentValues,
        this._searchArgs.options)
        .then(function (result) {
          this._throbber.exclude();
          if (this._searchArgs.modelFilter) {
            result = this._searchArgs.modelFilter.filter(result);
          }
          this.__tableModel.setDataAsMapArray(result, true, false);
          if (this._sortByColumn) {
            this.__tableModel.sortByColumn(this.__tableModel.getColumnIndexById(this._sortByColumn), true);
          }
        }, this);
    },

    __initWidgets : function(column_names, column_keys, extension, attribute) {
      // search filter field
      this._filter = new qx.ui.form.TextField().set({
        placeholder : this.tr("Search..."),
        liveUpdate : true,
        allowGrowX : true
      });
      this._filter.addListener("changeValue", qx.util.Function.debounce(this._applyFilter, 250, false), this);
      this._tableContainer = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
      this.__tableModel = new qx.ui.table.model.Simple();
      this.__tableModel.setColumns(column_names, column_keys);
      this.__table = new gosa.ui.table.Table(this.__tableModel);
      this.__table.setDecorator("table");
      this.__table.setStatusBarVisible(false);
      if (!this.__isSingleSelection) {
        this.__table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.MULTIPLE_INTERVAL_SELECTION);
      }
      this.__table.addListener("dblclick", this.__onOk, this);
      this._tableContainer.add(this.__table, {edge: 0});
      this.add(this._filter);
      this.add(this._tableContainer, {flex: 1});
      this.__table.setPreferenceTableName(extension + ":" + attribute + "Edit");


      // Add button static button line for the moment
      var paneLayout = new qx.ui.layout.HBox().set({
        spacing: 4, alignX : "right"
      });
      var buttonPane = new qx.ui.container.Composite(paneLayout).set({
        paddingTop: 11
      });

      var okButton;
      if (this.__isSingleSelection) {
        okButton = new qx.ui.form.Button(this.tr("OK"), "@Ligature/check/22");
      } else {
        okButton = new qx.ui.form.Button(this.tr("Add"), "@Ligature/plus/22");
      }

      okButton.setAppearance("button-primary");

      var cancelButton = new qx.ui.form.Button(this.tr("Cancel"), "@Ligature/ban/22");
      buttonPane.add(okButton);
      buttonPane.add(cancelButton);

      this.add(buttonPane);

      cancelButton.addListener("execute", this.close, this);
      okButton.addListener("execute", this.__onOk, this);
    },

    _applyFilter: function() {
      this._updateValues(this._filter.getValue());
    },

    __onOk : function() {
        var list = [];
        this.__table.getSelectionModel().iterateSelection(function(index) {
            list.push(this._detailsRpc === "searchForObjectDetails" ? this.__tableModel.getRowData(index)['__identifier__'] : this.__tableModel.getRowData(index));
          }, this);
        this.fireDataEvent("selected", list);
        this.close();
      }
   },

  destruct : function()
  {
    this._disposeObjects("__tableModel", "__table", "_tableContainer", "_filter", "_throbber");
  }
});