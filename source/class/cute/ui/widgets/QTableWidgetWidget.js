qx.Class.define("cute.ui.widgets.QTableWidgetWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){

    this.base(arguments);
    this.setDecorator("main");
    this.setLayout(new qx.ui.layout.Canvas());
    this._columnNames = [];
    this._tableData = [];
    this.addListener("appear", function(){
        this._createGui();
      }, this);


    this._resolvedNames = {};
  },

  members: {

    _table: null,
    _tableModel: null,
    _tableData: null,
    _columnNames: null,
    _columnIDs: null,
    _firstColumn: null,
    _resolvedNames: null,

    
    _createGui: function(){
      this._tableModel = new qx.ui.table.model.Simple();
      this._tableModel.setColumns(this._columnNames, this._columnIDs);
      this._table = new cute.ui.table.Table(this._tableModel);
      this._table.setPreferenceTableName(this.getExtension() + ":" + this.getAttribute());
      this._table.setStatusBarVisible(false);
      this._table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.MULTIPLE_INTERVAL_SELECTION);
      this._tableModel.setDataAsMapArray(this._tableData, true);
      this.add(this._table, {top:0 , bottom:0, right: 0, left:0});
      this._updatedTableData();
    },


    _updatedTableData: function(data){

      // Add the given widget-values as first element of the list.
      this._tableData = [];
      for(var i=0; i<this.getValue().getLength();i++){
        var row_data = {}
        row_data[this._firstColumn] = this.getValue().getItem(i);
        this._tableData.push(row_data);
      }

      // Get furhter object information
      this.__requestRowData(i);
    },

    __requestRowData: function(id){

      var rpc = cute.io.Rpc.getInstance();
      var values = this.getValue().toArray();

      var unknown_values = [];
      for(var i=0; i<values.length; i++){
        if(!(values[i] in this._resolvedNames)){
          unknown_values.push(values[i]);
        }
      }
      
      if(unknown_values.length){
        rpc.cA(function(result, error){
          if(error){
            new cute.ui.dialogs.Error(error.message).open();
            return;
          }else{
            for(var value in result['map']){
              this._resolvedNames[value] = result['result'][result['map'][value]];
            }
            this.__updateDataModel();
          }
        }, this, "getObjectDetails", this.getExtension(), this.getAttribute(), unknown_values, this._columnIDs);
      }else{
        this.__updateDataModel();
      }
    },

  
    __updateDataModel: function(){
      this._tableData = [];
      var values = this.getValue().toArray();
      for(var i=0; i<values.length; i++ ){
        this._tableData.push(this._resolvedNames[values[i]]);
      }
      this._tableModel.setDataAsMapArray(this._tableData);
    },
  

    _applyGuiProperties: function(props){
      this._columnNames = [];
      this._columnIDs = [];
      var first = null;
      for(var col in props['columns']){
        this._columnNames.push(props['columns'][col]);
        this._columnIDs.push(col);
        if(!first){
          first = col;
        }
      }
      this._firstColumn = first;
    }
  }
});
