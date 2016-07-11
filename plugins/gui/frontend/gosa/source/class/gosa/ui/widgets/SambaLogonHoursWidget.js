/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.widgets.SambaLogonHoursWidget", {

  extend : gosa.ui.widgets.Widget,

  construct: function(){

    this.base(arguments);
    this.contents.setLayout(new qx.ui.layout.Canvas());

    // Create a pane with a grid layout to place all the checkboxes
    var grid_l = new qx.ui.layout.Grid(2, 2);
    var pane = new qx.ui.container.Composite(grid_l);
    grid_l.setRowAlign(0, "center", "middle");
    grid_l.setRowAlign(1, "center", "middle");
    grid_l.setRowAlign(2, "center", "middle");
    this.contents.add(pane);
    pane.add(new qx.ui.basic.Label(this.tr("Hour")), {row: 0, column: 2, colSpan: 23});

    // Create the checkboxes and the controls
    var togglers = [];
    for(var d=0; d < 7; d++){

      // Center elements in the grid
      grid_l.setRowAlign(d+3, "center", "middle");

      // Add a day-name label in front of each row
      pane.add(new qx.ui.basic.Label(qx.locale.Date.getDayName("wide", d)), {row: d + 3, column: 0});

      // Add one checkbox per hour
      for(var h=0; h < 24; h++){
        var t = new qx.ui.form.CheckBox();
        pane.add(t, {row:d + 3, column: h + 1});
        togglers.push(t);
        t.addListener("changeValue", this.__updateValue, this);
      }

      // Add a toggle-row button
      var c = new qx.ui.form.ToggleButton("+/-");
      c.setBackgroundColor("gray");
      pane.add(c, {row: d + 3, column: 25});
      for(var x=0; x<24; x++){
        c.bind("value", togglers[x + (d * 24)], "value");
      }
    }

    // Add toggle-column button
    for(var h=0; h < 24; h++){
      var c = new qx.ui.form.ToggleButton("+/-");
      c.setBackgroundColor("gray");
      pane.add(new qx.ui.basic.Label(h.toString()), {row: 1 , column: h + 1});
      pane.add(c, {row: 2 , column: h + 1});
      for(var x=0; x< 7; x++){
        c.bind("value", togglers[ (x * 24) + h], "value");
      }
    }
    this.contents.add(pane, {left:10, top: 10});
    this.togglers = togglers;
  },

  statics: {
    
    /* Create a readonly representation of this widget for the given value.
     * This is used while merging object properties.
     * */
    getMergeWidget: function(value){
      var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      for(var i=0;i<value.getLength(); i++){
        var w = new qx.ui.form.TextField(value.getItem(i));
        w.setReadOnly(true);
        container.add(w);
      }
      return(container);
    }
  },    

  members: {
    togglers: null,
    _property_timer: null,


    /* This method updates the value-property and sends the "changeValue" 
     * event after a period of time, to tell the object-proxy that values have changed.
     *
     * This is a method which can be used as listener for value updates.
     * See "_createWidget" for details.
     * */
    _propertyUpdaterTimed: function(new_data){

      var timer = qx.util.TimerManager.getInstance();
      if(this._property_timer != null){
        timer.stop(this._property_timer);
        this._property_timer = null;
      }
      this._property_timer = timer.start(function(){
          timer.stop(this._property_timer);
          this._property_timer = null;
          this.fireDataEvent("changeValue", new_data);
        }, null, this, null, 1000);
    },


    /* Send a value-update to the object
     * */
    __updateValue: function(){
      if(!this.getInitComplete()){
        return;
      }
      var bits = "";
      for(var day=0; day < 7; day++){
        for(var hour=0; hour< 24; hour ++){
          bits += this.togglers[(day*24)+hour].getValue() ? "1" : "0";
        }
      }
      var new_data = new qx.data.Array([bits]);
      this._propertyUpdaterTimed(new_data);
    },

    /* Process incoming values
     * */
    _applyValue: function(value){
      if(!this.isDisposed() && value.getLength()){
        for(var day=0; day < 7; day++){
          for(var hour=0; hour< 24; hour ++){
            this.togglers[(day*24)+hour].setValue(value.getItem(0)[(day * 24) + hour] == 1);
          }
        }
      }
    }
  }
});
