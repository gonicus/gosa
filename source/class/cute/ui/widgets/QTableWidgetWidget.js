qx.Class.define("cute.ui.widgets.QTableWidgetWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){

    this.base(arguments);
    this.setDecorator("main");
    this.setLayout(new qx.ui.layout.Canvas());
    this._columNames = [];
    this._tableData = [];
    this.addListener("appear", function(){
        this._createGui();
      }, this);
  },

  members: {

    _table: null,
    _tableModel: null,
    _tableData: null,
    _columNames: null,

    
    _createGui: function(){
      this._tableModel = new qx.ui.table.model.Simple(this._tableData);

      this._tableModel.setColumns(this._columNames);

      var data = [];
      for(var i=0; i<this.getValue().getLength();i++){
        this._tableData.push([this.getValue().getItem(i)]);
      }
      this._tableModel.setData(this._tableData);
      this._table = new qx.ui.table.Table(this._tableModel);
      this._table.setStatusBarVisible(false);
      this.add(this._table, {top:0 , bottom:0, right: 0, left:0});
    },


    _applyGuiProperties: function(props){
      this._columNames = [];
      for(var col in props['columns']){
        this._columNames.push(props['columns'][col]);
      }
    }
  }
});
