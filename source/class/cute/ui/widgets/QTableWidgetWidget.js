qx.Class.define("cute.ui.widgets.QTableWidgetWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){

    this.base(arguments);
    this.setDecorator("main");
    this.setLayout(new qx.ui.layout.Canvas());
    this._columnNames = [];
    this._tableData = [];
    this._resolvedNames = {};

    // Take care of value modification
    this.addListener("appear", function(){
        this._createGui();
        this._updatedTableData();
      }, this);
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
      this._table.setStatusBarVisible(false);
      this._table.getSelectionModel().setSelectionMode(qx.ui.table.selection.Model.MULTIPLE_INTERVAL_SELECTION);
      this.add(this._table, {top:0 , bottom:0, right: 0, left:0});
      this._table.setPreferenceTableName(this.getExtension() + ":" + this.getAttribute());

      // Add new group membership
      var b = new qx.ui.form.Button("test");
      b.addListener("execute", function(){
          this.getValue().push("acltest");
          this.fireDataEvent("changeValue", new qx.data.Array(this.getValue().toArray()));
        }, this);
      this.add(b);

      // Add a remove listener
      this._table.addListener("remove", function(e){
        var that = this;
        this._table.getSelectionModel().iterateSelection(function(index) {
            var selected = that._tableModel.getRowData(index)["__indentifier__"];
            that.getValue().remove(selected);
          });
        this.fireDataEvent("changeValue", new qx.data.Array(this.getValue().toArray()));
      }, this);
    },


    /* Update the table model and try to resolve missing values.
     * */
    _updatedTableData: function(data){
      this.__updateDataModel();
      this.__resolveMissingValues();
    },


    /* Applies a new value for this widget
     * */
    _applyValue: function(value){

      // Add a listener to the content array.
      // On each modification update the table model.
      console.log(value.toArray());
      if(value){
        value.addListener("change", function(){
            this._updatedTableData();        
          },this);
      }
      this._updatedTableData();        
    },


    /* Resolve missing value information
     * */
    __resolveMissingValues: function(){

      var rpc = cute.io.Rpc.getInstance();
      var values = this.getValue().toArray();

      var unknown_values = [];
      for(var i=0; i<values.length; i++){
        if(!(values[i] in this._resolvedNames)){
          unknown_values.push(values[i]);

          var row_data = {}
          row_data[this._firstColumn] = values[i];
          row_data["__indentifier__"] = values[i];
          this._resolvedNames[values[i]] = row_data;
        }
      }
      
      if(unknown_values.length){
        rpc.cA(function(result, error){
          if(error){
            new cute.ui.dialogs.Error(error.message).open();
            return;
          }else{
            for(var value in result['map']){
              var data = result['result'][result['map'][value]];
              if(data){
                data['__indentifier__'] = value;
                this._resolvedNames[value] = data;
              }
            }
            this.__updateDataModel();
          }
        }, this, "getObjectDetails", this.getExtension(), this.getAttribute(), unknown_values, this._columnIDs);
      }else{
        this.__updateDataModel();
      }
    },


    /* Set the visible content of the table.
     * */
    __updateDataModel: function(){
      if(!this._table){
        return;
      }
      this._tableData = [];
      var values = this.getValue().toArray();
      for(var i=0; i<values.length; i++ ){
        if(values[i] in this._resolvedNames){
          row_data = this._resolvedNames[values[i]];
        }else{
          var row_data = {}
          row_data[this._firstColumn] = values[i];
        }
        this._tableData.push(row_data);
      }
      this._tableModel.setDataAsMapArray(this._tableData, true, false);
      this._table.sort();
    },
  

    /* Apply porperties that were defined in the ui-tempalte.
     *
     * Collect column names here.
     * */
    _applyGuiProperties: function(props){
      this._columnNames = [];
      this._columnIDs = [];
      var first = null;
      for(var col in props['columns']){
        this._columnNames.push(this.tr(props['columns'][col]));
        this._columnIDs.push(col);
        if(!first){
          first = col;
        }
      }
      this._firstColumn = first;
    }
  }
});
