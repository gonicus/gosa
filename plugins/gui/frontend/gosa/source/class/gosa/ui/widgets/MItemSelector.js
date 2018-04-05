/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2018 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/**
* TODO: add documentation
*/
qx.Mixin.define('gosa.ui.widgets.MItemSelector', {

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct: function () {
    this._columnSettings = {names: [], ids: [], renderers: [], widths: []};
    this._selectorOptions = {};
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties: {
    single: {
      check: 'Boolean',
      init: false
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members: {
    _modelFilter: null,
    _sortByColumn: null,
    _columnSettings: null,
    _selectorOptions: null,
    _contextMenuConfig: null,
    _firstColumn: null,

    openSelector :  function() {
      var d = new gosa.ui.dialogs.ItemSelector(
        this['tr'](this._editTitle),
        this.getValue().toArray(),
        this.getExtension(),
        this.getAttribute(),
        this._columnSettings,
        this.isSingle(),
        this._modelFilter,
        this._sortByColumn,
        null,
        this._selectorOptions);

      d.addListener("selected", this._onSelected, this);

      this._getController().addDialog(d);
      d.open();
    },

    _createModelFilter: function () {
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

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct: function () {
    this._columnSettings = null;
    this._firstColumn = null;
    this._selectorOptions = null;
  }
});
