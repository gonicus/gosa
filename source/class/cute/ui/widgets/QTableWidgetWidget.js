qx.Class.define("cute.ui.widgets.QTableWidgetWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
  
    this.base(arguments);
    this.setLayout(new qx.ui.layout.Canvas());
    this._attributes = [];
  },

  members: {

    _attributes: null,
    _table: null,
    _tableModel: null,
  
    _applyGuiProperties: function(props){

      var columns = [];
      for(var col in props['columns']){
        columns.push(props['columns'][col]);
      }
      this._tableModel = new qx.ui.table.model.Simple();
      this._tableModel.setColumns(columns);
      this._table = new qx.ui.table.Table(this._tableModel);
      this.add(this._table, {top:0 , bottom:0, right: 0, left:0});
    }
  }
});
