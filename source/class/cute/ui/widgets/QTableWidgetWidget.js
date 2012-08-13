qx.Class.define("cute.ui.widgets.QTableWidgetWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
  
    this.base(arguments);
    this.setLayout(new qx.ui.layout.Canvas());

    var widget = new qx.ui.table.Table();
    this.add(widget, {top:0 , bottom:0, right: 0, left:0});
  },

  members: {
  
    _applyGuiProperties: function(props){

      console.log(props);
    }
  }
});
