/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/*
#asset(gosa/*)
*/

qx.Class.define("gosa.ui.dialogs.ItemSelector", {

  extend: gosa.ui.dialogs.Dialog,

  construct: function(title, current_values, extension, attribute, column_keys, column_names, single) {
    this.base(arguments);
    this.setCaption(title);
    this.setResizable(true, true, true, true);
    this.setWidth(500);
    this.setLayout(new qx.ui.layout.VBox(0));

    this.__isSingleSelection = !!single;

    this.__initWidgets(column_names, column_keys, extension, attribute);

    // init table model
    gosa.io.Rpc.getInstance().cA("searchForObjectDetails", extension, attribute, "", column_keys, current_values)
      .then(function(result) {
        console.log(result);
        this.__tableModel.setDataAsMapArray(result, true, false);
      }, this);
  },

  events: {
    "selected": "qx.event.type.Data"
  },

  members : {
    __table : null,
    __tableModel : null,
    __isSingleSelection : false,

    __initWidgets : function(column_names, column_keys, extension, attribute) {
      this.__tableModel = new qx.ui.table.model.Simple();
      this.__tableModel.setColumns(column_names, column_keys);
      this.__table = new gosa.ui.table.Table(this.__tableModel);
      this.__table.setDecorator("table");
      this.__table.setStatusBarVisible(false);
      if (!this.__isSingleSelection) {
        this.__table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.MULTIPLE_INTERVAL_SELECTION);
      }
      this.__table.addListener("dblclick", this.__onOk, this);
      this.add(this.__table, {flex: 1});
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

    __onOk : function() {
        var list = [];
        this.__table.getSelectionModel().iterateSelection(function(index) {
            list.push(this.__tableModel.getRowData(index)['__identifier__']);
          }, this);
        this.fireDataEvent("selected", list);
        this.close();
      }
   },

  destruct : function()
  {
    this._disposeObjects("__tableModel", "__table");
  }
});
