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
  include: gosa.ui.table.MColumnSettings,

  construct: function(title, current_values, extension, attribute, columnSettings, single, modelFilter, sortByColumn, mode, options) {
    this.base(arguments);
    this.setCaption(title);
    this.setResizable(true, true, true, true);
    this.setWidth(500);
    this.setLayout(new qx.ui.layout.VBox(0));
    this._sortByColumn = sortByColumn;

    this.__isSingleSelection = !!single;

    this._detailsRpc = mode || "searchForObjectDetails";

    var searchOptions = {};
    var queryFilter =  "";
    if (options && options.hasOwnProperty('queryFilter')) {
      queryFilter = options.queryFilter;
    } else {
      searchOptions.limit = 100;
    }
    if (modelFilter) {
      searchOptions.filter = modelFilter.getSearchOptions();
    }

    if (searchOptions.hasOwnProperty("filter") && searchOptions.filter.hasOwnProperty("_type")) {
      this._allowedTypes = qx.lang.Object.clone(searchOptions.filter._type);
    }

    this._selectorOptions = options || {};

    this._searchArgs = {
      extension: extension,
      attribute: attribute,
      queryFilter: queryFilter,
      columnKeys: columnSettings.ids,
      currentValues: current_values,
      options: searchOptions,
      modelFilter: modelFilter
    };

    this.__initWidgets(columnSettings, extension, attribute);

    if (!this._selectorOptions.skipInitialSearch) {
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
    _columnSettings: null,
    _allowedTypes: null,
    _selectorOptions: null,


    _updateValues: function() {
      var queryFilter = this._searchArgs.queryFilter;
      if (this.hasChildControl("search-field")) {
        queryFilter = this.getChildControl("search-field").getValue() || this._searchArgs.queryFilter;
      }
      if (this.hasChildControl("type-selector")) {
        var selection = this.getChildControl("type-selector").getSelection();
        var selectedTypes = [];
        selection.forEach(function(sel) {
          if (sel.getUserData("type")) {
            selectedTypes.push(sel.getUserData("type"));
          }
        });
        if (selectedTypes.length > 0) {
          this._searchArgs.options.filter._type = selectedTypes;
        }
      }
      if (this.hasChildControl("base-selector")) {
        var selectedParentDn = gosa.ui.widgets.Widget.getSingleValue(this.getChildControl("base-selector").getValue());
        if (selectedParentDn) {
          this._searchArgs.options.filter[this._selectorOptions.filters.base.use] = "%,"+selectedParentDn;
        } else {
          delete this._searchArgs.options.filter[this._selectorOptions.filters.base.use];
        }
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

    __initWidgets : function(columnSettings, extension, attribute) {
      if (this._selectorOptions.hasOwnProperty("filters")) {
        this._createChildControl("filter-button");
        for (var filterName in this._selectorOptions.filters) {
          switch (filterName) {
            case "search":
              if (this._selectorOptions.filters.search === true) {
                // search filter field
                this._createChildControl('search-field');
              }
              break;

            case "base":
              var control = this.getChildControl('base-selector');
              control.setObjectTypes(this._allowedTypes);
              break;

            case "type":
              if (this._allowedTypes) {
                var control = this.getChildControl('type-selector');
                control.add(new qx.ui.form.ListItem(""));
                this._allowedTypes.forEach(function(type) {
                  var item = new qx.ui.form.ListItem(this['tr'](type));
                  item.setUserData("type", type);
                  control.add(item);
                }, this);
              }
              break;

            default:
              this.warn("unsupported filter type: ", filterName);
              break;
          }
        }
      }

      this._tableContainer = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
      this.__tableModel = new qx.ui.table.model.Simple();
      this.__tableModel.setColumns(columnSettings.names, columnSettings.ids);
      this.__table = new gosa.ui.table.Table(this.__tableModel);
      this.__table.setDecorator("table");
      this.__table.setStatusBarVisible(false);
      if (!this.__isSingleSelection) {
        this.__table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.MULTIPLE_INTERVAL_SELECTION);
      }
      this.__table.addListener("dblclick", this.__onOk, this);
      this._tableContainer.add(this.__table, {edge: 0});

      this.add(this._tableContainer, {flex: 1});
      this.__table.setPreferenceTableName(extension + ":" + attribute + "Edit");

      this._applyColumnSettings(this.__table, columnSettings);


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

    __onOk : function() {
      var list = [];
      this.__table.getSelectionModel().iterateSelection(function(index) {
        list.push(this._detailsRpc === "searchForObjectDetails" ? this.__tableModel.getRowData(index)['__identifier__'] : this.__tableModel.getRowData(index));
      }, this);
      this.fireDataEvent("selected", list);
      this.close();
    },

    __maintainSearchButton: function() {
      if (!this.hasChildControl("filter-button")) {
        return;
      }
      var button = this.getChildControl("filter-button");
      if (this.hasChildControl("search-field") && this.getChildControl("search-field").getValue()) {
        button.setEnabled(true);
        return;
      }
      if (this.hasChildControl("type-selector")) {
        var selection = this.getChildControl("type-selector").getSelection();
        var selectedTypes = [];
        selection.forEach(function(sel) {
          if (sel.getUserData("type")) {
            selectedTypes.push(sel.getUserData("type"));
          }
        });
        if (selectedTypes.length > 0) {
          button.setEnabled(true);
          return;
        }
      }
      if (this.hasChildControl("base-selector")) {
        if (gosa.ui.widgets.Widget.getSingleValue(this.getChildControl("base-selector").getValue())) {
          button.setEnabled(true);
          return;
        }
      }

      button.setEnabled(false);
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {
        case 'filter-container':
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox(8));
          this.add(control);
          break;

        case 'search-field':
          control = new qx.ui.form.TextField().set({
            placeholder: this.tr("Search..."),
            liveUpdate: true,
            allowGrowX: true
          });
          var debouncedUpdate = qx.util.Function.debounce(this._updateValues, 500, false).bind(this);
          control.addListener("changeValue", function() {
            debouncedUpdate();
            this.__maintainSearchButton();
          }, this);
          var label = new qx.ui.basic.Label(this.tr("Search"));
          var container = new qx.ui.container.Composite(new qx.ui.layout.HBox());
          container.add(label, {width: "20%"});
          container.add(control, {flex: 1});
          this.getChildControl('filter-container').addAt(container, 3);
          break;

        case 'type-selector':
          control = new qx.ui.form.SelectBox();
          control.addListener("changeSelection", this.__maintainSearchButton, this);
          var label = new qx.ui.basic.Label(this.tr("Type"));
          var container = new qx.ui.container.Composite(new qx.ui.layout.HBox());
          container.add(label, {width: "20%"});
          container.add(control, {flex: 1});
          this.getChildControl('filter-container').addAt(container, 2);
          break;

        case 'base-selector':
          control = new gosa.ui.widgets.QBaseSelectorWidget();
          control.addListener("resize", function () {
            this.center();
          }, this);
          control.addListener("changeValue", this.__maintainSearchButton, this);
          this.getChildControl('filter-container').addAt(new qx.ui.basic.Label(this.tr("Select Base")), 0);
          this.getChildControl('filter-container').addAt(control, 1);
          break;

        case 'filter-button':
          control = new qx.ui.form.Button(this.tr("Filter"));
          control.setEnabled(false);
          this.getChildControl('filter-container').addAt(control, 4);
          control.addListener("execute", this._updateValues, this);
          break;
      }

      return control || this.base(arguments, id);
    }

  },

  destruct : function()
  {
    this._disposeObjects("__tableModel", "__table", "_tableContainer", "_filter", "_throbber");
  }
});