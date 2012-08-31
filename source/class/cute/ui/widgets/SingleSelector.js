qx.Class.define("cute.ui.widgets.SingleSelector", {

  extend: cute.ui.widgets.Widget,

  construct: function(){

    this.base(arguments);
    this.setLayout(new qx.ui.layout.HBox(0));
    this._columnNames = [];
    this._columnIDs = [];
    this._resolvedNames = {};

    // Take care of value modification
    this.addListener("appear", function(){
        this._createGui();
        this.__updateVisibleText();
      }, this);
  },

  members: {

    _table: null,
    _tableModel: null,
    _tableData: null,
    _columnNames: null,
    _editTitle: "",
    _columnIDs: null,
    _firstColumn: null,
    _resolvedNames: null,
    _widget: null,
    _delButton: null,


    _applyValue: function(){
      this.__updateVisibleText();
    },

    __updateVisibleText: function(){
      if(this._widget){
        if(this.getValue().getLength()){
          var name = this.getValue().getItem(0);
          if(name in this._resolvedNames){
            this._widget.setValue(this._resolvedNames[name][this._columnIDs[0]]);
          }else{
            this._widget.setValue(this.tr("pending ..."));
            this.__resolveMissingValues();
          }
        }else{
          this._widget.setValue("");
        }
      }
      if(this._delButton){
        if(this.getValue().getLength()){
          this._delButton.setLabel("-");
        }else{
          this._delButton.setLabel("+");
        }
      }
    },

    
    _createGui: function(){
      this._widget = new qx.ui.form.TextField("value later ..");
      this._widget.setEnabled(false);
      this._delButton = new qx.ui.form.Button("-");
      this.add(this._widget, {flex: 1});
      this.add(this._delButton);

      if(!this.getExtension() || !this.getAttribute()){
        this.error("unabled to load SingleSelector, no bindings given!");
        return;
      }

      this._delButton.addListener("execute", function(){
          var value = this.getValue();
          if(value.getLength()){
            value.removeAll();
            this._applyValue(value);
            this.fireDataEvent("changeValue", this.getValue().copy());
          }else{
            var d = new cute.ui.ItemSelector(this.tr(this._editTitle), this.getValue().toArray(), 
              this.getExtension(), this.getAttribute(), this._columnIDs, this._columnNames);

            d.addListener("selected", function(e){
              if(e.getData().length){
                this.getValue().removeAll();
                this.getValue().push(e.getData()[0]);
                this.fireDataEvent("changeValue", this.getValue().copy());
                this.__resolveMissingValues();
              }
            }, this);

            d.open();
        }
          }, this);

      return;
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
          row_data["__identifier__"] = values[i];
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
                data['__identifier__'] = value;
                this._resolvedNames[value] = data;
              }
            }
            this.__updateVisibleText();
          }
        }, this, "getObjectDetails", this.getExtension(), this.getAttribute(), unknown_values, this._columnIDs);
      }else{
        this.__updateVisibleText();
      }
    },


    /* Apply porperties that were defined in the ui-tempalte.
     *
     * Collect column names here.
     * */
    _applyGuiProperties: function(props){
      if('editTitle' in props && 'string' in props['editTitle']){
        this._editTitle = props['editTitle']['string'];
      }
      this._columnNames = [];
      this._columnIDs = [];
      var first = null;
      if('columns' in props){
        for(var col in props['columns']){
          this._columnNames.push(this.tr(props['columns'][col]));
          this._columnIDs.push(col);
          if(!first){
            first = col;
          }
        }
      }
      this._firstColumn = first;
    }
  }
});
