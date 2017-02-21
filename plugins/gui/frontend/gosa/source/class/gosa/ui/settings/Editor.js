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
* Generic settings editor.
*/
qx.Class.define("gosa.ui.settings.Editor", {
  extend : qx.ui.core.Widget,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(namespace) {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.VBox());
    this.setNamespace(namespace);

    this.addListenerOnce("appear", this.__initTable, this);
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    title: {
      check: "String",
      nullable: true,
      apply: "_applyTitle"
    },

    namespace: {
      check: "String",
      init: "",
      apply: "_applyNamespace"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __handler: null,

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {
        case "title":
          control = new qx.ui.basic.Label(this.tr("Editor"));
          this._add(control);
          break;

        case "table":
          var propertyEditor_resizeBehaviour = {
            tableColumnModel : function(obj) {
              return new qx.ui.table.columnmodel.Resize(obj);
            }
          };
          control = new qx.ui.table.Table(null, propertyEditor_resizeBehaviour);
          this._add(control, {flex: 1});
          break;
      }

      return control || this.base(arguments, id);
    },

    // property apply
    _applyNamespace: function(value) {
      this.__handler = gosa.data.SettingsRegistry.getHandlerForPath(value);
    },

    __initTable: function() {

      var itemInfos = this.__handler.getItemInfos();
      var tableData = [];
      Object.getOwnPropertyNames(itemInfos).forEach(function(path) {
        var options = {};
        if (itemInfos[path].type) {
          options.type = itemInfos[path].type;
          if (options.type === "boolean" && qx.lang.Type.isString(itemInfos[path].value)) {
            itemInfos[path].value = itemInfos[path].value.toLowerCase() === "true";
          }
        }
        if (itemInfos[path].options) {
          options.options = itemInfos[path].options;
        }
        tableData.push([path, itemInfos[path].title||path, itemInfos[path].value, options]);
      }, this);

      // create the  "meta" cell renderer object
      var propertyCellRendererFactory = new qx.ui.table.cellrenderer.Dynamic(this.__propertyCellRendererFactoryFunc);

      // create a "meta" cell editor object
      var propertyCellEditorFactory = new qx.ui.table.celleditor.Dynamic(this.__propertyCellEditorFactoryFunc);

      // create table
      var propertyEditor_tableModel = new qx.ui.table.model.Simple();
      propertyEditor_tableModel.setColumns(
      [
        this.tr('Path'),
        this.tr('Title'),
        this.tr('Value')
      ]);

      var propertyEditor = this.getChildControl("table");
      propertyEditor.setTableModel(propertyEditor_tableModel);

      // remove decor
      propertyEditor.setDecorator(null);

      // layout
      propertyEditor.setColumnVisibilityButtonVisible(false);
      propertyEditor.setKeepFirstVisibleRowComplete(true);
      propertyEditor.setStatusBarVisible(false);

      // selection mode
      propertyEditor.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.SINGLE_SELECTION);

      // Get the table column model
      var tcm = propertyEditor.getTableColumnModel();

      // first table columns is not visible, has the key
      tcm.setColumnVisible(0, false);
      propertyEditor_tableModel.sortByColumn(0, true);

      // second column has the label

      // third column for editing the value and has special cell renderers
      // and cell editors
      propertyEditor_tableModel.setColumnEditable(2, true);
      tcm.setDataCellRenderer(2, propertyCellRendererFactory);
      tcm.setCellEditorFactory(2, propertyCellEditorFactory);

      // fourth column is not visible, has the metadata

      // set data
      propertyEditor.getTableModel().setData(tableData);

      var model = propertyEditor.getTableModel();
      // create event listener for data change event. this would normally
      // send the data back to the server etc.
      propertyEditor.getTableModel().addListener("dataChanged", function(event) {
        if ( !(event instanceof qx.event.type.Data)) {
          return;
        }
        var changedData = event.getData();

        // get changed data
        var key = model.getValue(0,changedData.firstRow);
        var value = model.getValue(changedData.firstColumn, changedData.firstRow);

        gosa.io.Rpc.getInstance().cA("changeSetting", this.getNamespace()+"."+key, value)
        .catch(gosa.ui.dialogs.Error.show);
      }, this);

      return propertyEditor;
    },

    __propertyCellRendererFactoryFunc : function (cellInfo)
    {
      var table = cellInfo.table;
      var tableModel = table.getTableModel();
      var rowData = tableModel.getRowData(cellInfo.row);
      var metaData = rowData[3];
      var renderer;

      for ( var cmd in metaData ) {

        switch ( cmd ) {
          case "type":

            switch ( metaData['type'])
            {
              case "boolean":
                return new qx.ui.table.cellrenderer.Boolean;

              case "password":
                return new qx.ui.table.cellrenderer.Password;
            }
            break;

          case "options":
            renderer = new qx.ui.table.cellrenderer.Replace;
            var replaceMap = {};
            metaData['options'].forEach(function(row){
              if (row instanceof Array)
              {
                replaceMap[row[0]]=row[2];
              }
            });
            renderer.setReplaceMap(replaceMap);
            renderer.addReversedReplaceMap();
            return renderer;
        }
      }
      return new qx.ui.table.cellrenderer.Default();
    },

    // cell editor factory function
    // returns a cellEditorFactory instance based on data in the row itself
    __propertyCellEditorFactoryFunc: function (cellInfo) {
      var table = cellInfo.table;
      var tableModel = table.getTableModel();
      var rowData = tableModel.getRowData(cellInfo.row);
      var metaData = rowData[3];
      var cellEditor = new qx.ui.table.celleditor.TextField;
      var validationFunc = null;

      for ( var cmd in metaData )
      {
        switch ( cmd )
        {
          case "options":
            if (metaData.editable)
            {
              cellEditor = new qx.ui.table.celleditor.ComboBox();
            }
            else
            {
              cellEditor = new qx.ui.table.celleditor.SelectBox();
            }
            cellEditor.setListData( metaData['options'] );
            break;

          case "editable":
            break;

          case "type":
            switch ( metaData['type'] )
            {
              case "password":
                cellEditor = new qx.ui.table.celleditor.PasswordField;
                break;

              case "boolean":
                cellEditor = new qx.ui.table.celleditor.CheckBox;
                break;

              case "email":
                cellEditor.setValidationFunction (
                function( newValue, oldValue )
                {
                  var re = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*\.(\w{2}|(com|net|org|edu|int|mil|gov|arpa|biz|aero|name|coop|info|pro|museum))$/;
                  if ( re.test(newValue) )
                  {
                    return newValue;
                  }
                  alert("You did not enter a valid email address");
                  return oldValue;
                });
                break;
            }
            break;

          case "regExp":
            cellEditor.setValidationFunction (
            function( newValue, oldValue )
            {
              var re = new RegExp(metaData['regExp']);
              if ( re.test(newValue) )
              {
                return newValue;
              }
              alert(metaData['failMsg']);
              return oldValue;
            });
            break;

          case "validationFunc":
            cellEditor.setValidationFunction (metaData['validationFunc']);
            break;

          case "required":
            validationFunc = function( newValue, oldValue )
            {
              if (! newValue)
              {
                alert(this.tr("You need to supply a value here"));
                return oldValue;
              }
              return newValue;
            };
            break;
        }
      }
      return cellEditor;
    },

    // property apply
    _applyTitle: function(value) {
      var control = this.getChildControl("title");
      if (value) {
        control.setValue(value);
        control.show();
      } else {
        control.exclude();
      }
    }
  }
});