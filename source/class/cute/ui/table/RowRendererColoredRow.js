qx.Class.define("cute.ui.table.RowRendererColoredRow",
{
  extend: qx.ui.table.rowrenderer.Default,

  construct: function(){
    this.base(arguments);
    this.colorRows = [];
  },

  destruct: function(){
    this.colorRows = null;
  },

  members: {

    colorRows: null,

    updateDataRowElement : function(rowInfo, rowElem)
    {
      var fontStyle = this.__fontStyle;
      var style = rowElem.style;

      // set font styles
      qx.bom.element.Style.setStyles(rowElem, fontStyle);

      if (rowInfo.focusedRow && this.getHighlightFocusRow()){
        style.backgroundColor = rowInfo.selected ? this._colors.bgcolFocusedSelected : this._colors.bgcolFocused;
      }else{
        if (rowInfo.selected){
          style.backgroundColor = this._colors.bgcolSelected;
        }else{
          style.backgroundColor = (rowInfo.row % 2 == 0) ? this._colors.bgcolEven : this._colors.bgcolOdd;
        }
      }

      for(var id in this.colorRows){
        var item = this.colorRows[id]; 
        if(rowInfo['rowData'][item['where']] == item['match']){
          style.backgroundColor = item['color'];
          break;
        }
      }
      style.color = rowInfo.selected ? this._colors.colSelected : this._colors.colNormal;
      style.borderBottom = "1px solid " + this._colors.horLine;
    },

    // interface implementation
    createRowStyle : function(rowInfo)
    {
      var rowStyle = [];
      rowStyle.push(";");
      rowStyle.push(this.__fontStyleString);
      rowStyle.push("background-color:");

      var colorSet = false;
      for(var id in this.colorRows){
        var item = this.colorRows[id]; 
        if(rowInfo['rowData'][item['where']] == item['match']){
          rowStyle.push(item['color']);
          colorSet = true;
          break;
        }
      }

      if(!colorSet){
        if (rowInfo.focusedRow && this.getHighlightFocusRow()){
          rowStyle.push(rowInfo.selected ? this._colors.bgcolFocusedSelected : this._colors.bgcolFocused);
        }else{
          if (rowInfo.selected){
            rowStyle.push(this._colors.bgcolSelected);
          }else{
            rowStyle.push((rowInfo.row % 2 == 0) ? this._colors.bgcolEven : this._colors.bgcolOdd);
          }
        }
      }

      rowStyle.push(';color:');
      rowStyle.push(rowInfo.selected ? this._colors.colSelected : this._colors.colNormal);
      rowStyle.push(';border-bottom: 1px solid ', this._colors.horLine);
      return rowStyle.join("");
    } 
  }
});
