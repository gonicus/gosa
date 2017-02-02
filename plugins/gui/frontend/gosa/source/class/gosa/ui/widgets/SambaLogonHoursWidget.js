/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

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
    var grid_l = new qx.ui.layout.Grid();
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
      grid_l.setRowAlign(d + 2, "center", "middle");

      // Add a day-name label in front of each row
      var rtb = new qx.ui.form.ToggleButton(qx.locale.Date.getDayName("wide", d));
      rtb.setAppearance("button-link");
      pane.add(rtb, {row: d + 2, column: 0});

      // Add one checkbox per hour
      for(var h=0; h < 24; h++){
        var t = new qx.ui.form.CheckBox();
        t.setAllowGrowX(true);
        t.setCenter(true);
        pane.add(t, {row:d + 2, column: h + 1});
        togglers.push(t);
        t.addListener("changeValue", this.__updateValue, this);

        if (d === 0) {
          t.setBackgroundColor("rgba(255, 10, 10, " + (h % 2 ? 0.15 : 0.1) + ")");
        }
        else {
          t.setBackgroundColor("rgba(100, 100, 100, " + (h % 2 ? 0.1 : 0.0) + ")");
        }
      }

      // Bind toggler
      for(var x=0; x<24; x++){
        rtb.bind("value", togglers[x + (d * 24)], "value");
      }
    }

    // Add toggle-column button
    for(var h=0; h < 24; h++){
      var tb = new qx.ui.form.ToggleButton(h.toString());
      tb.setAppearance("button-link");
      pane.add(tb, {row: 1 , column: h + 1});
      for(var x=0; x< 7; x++){
        tb.bind("value", togglers[ (x * 24) + h], "value");
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
