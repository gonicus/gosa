/*
#asset(cute/*)
*/

qx.Class.define("cute.ui.ItemSelector", {

  extend: cute.ui.dialogs.Dialog,

  construct: function(title, current_values, extension, attribute, column_keys, column_names, single){

    this.base(arguments);
    this.setCaption(title);

    this.setResizable(true, true, true, true);
    this.setWidth(500);
    this.setLayout(new qx.ui.layout.VBox(0));
    var tableModel = new qx.ui.table.model.Simple();
    tableModel.setColumns(column_names, column_keys);
    var table = new cute.ui.table.Table(tableModel);
    table.setStatusBarVisible(false);
    if (!single) {
      table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.MULTIPLE_INTERVAL_SELECTION);
    }
    this.add(table, {flex: 1});
    table.setPreferenceTableName(extension + ":" + attribute + "Edit");

    var rpc = cute.io.Rpc.getInstance();
    rpc.cA(function(result, error){
        tableModel.setDataAsMapArray(result, true, false);
      },this, "searchForObjectDetails", extension, attribute, "", column_keys, current_values);

    // Add button static button line for the moment
    var paneLayout = new qx.ui.layout.HBox().set({
      spacing: 4, alignX : "right"
    });
    var buttonPane = new qx.ui.container.Composite(paneLayout).set({
      paddingTop: 11
    });

    var okButton;
    if (single) {
       okButton = new qx.ui.form.Button(this.tr("Choose"), cute.Config.getImagePath("actions/dialog-ok.png", 22));
    } else {
       okButton = new qx.ui.form.Button(this.tr("Add"), cute.Config.getImagePath("actions/list-add.png", 22));
    }
    var cancelButton = new qx.ui.form.Button(this.tr("Cancel"), cute.Config.getImagePath("actions/dialog-cancel.png", 22));
    buttonPane.add(okButton);
    buttonPane.add(cancelButton);

    this.add(buttonPane);

    cancelButton.addListener("execute", this.close, this);
    okButton.addListener("execute", this._ok, this);
    table.addListener("dblclick", this._ok, this);

    this.__table = table;
    this.__tableModel = tableModel;
  }, 

  events: {
    "selected": "qx.event.type.Data"
  },

  members : {
    __table : null,
    __tableModel : null,

    _ok : function() {
        var list = [];
        this.__table.getSelectionModel().iterateSelection(function(index) {
            list.push(this.__tableModel.getRowData(index)['__identifier__']);
          }, this);
        this.fireDataEvent("selected", list);
        this.close();
      }
   }
});
