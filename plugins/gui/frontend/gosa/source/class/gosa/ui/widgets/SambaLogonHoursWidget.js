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

    this.__createPane();
    this.__createCheckBoxes();
    this.__createDayButtons();
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
    __togglers: null,
    __propertyTimer: null,
    __pane : null,
    __gridLayout : null,

    __createPane : function() {
      this.__gridLayout = new qx.ui.layout.Grid();
      this.__pane = new qx.ui.container.Composite(this.__gridLayout);

      this.__gridLayout.setRowAlign(0, "center", "middle");
      this.__gridLayout.setRowAlign(1, "center", "middle");
      this.__gridLayout.setRowAlign(2, "center", "middle");

      this.contents.add(this.__pane);
      this.__pane.add(new qx.ui.basic.Label(this.tr("Hour")), {row: 0, column: 2, colSpan: 23});
      this.contents.add(this.__pane, {left: 10, top: 10});
    },

    __createCheckBoxes : function() {
      this.__togglers = [];
      for (var d = 0; d < 7; d++) {

        // Center elements in the grid
        this.__gridLayout.setRowAlign(d + 2, "center", "middle");

        // Add a day-name label in front of each row
        var toggleButton = new qx.ui.form.ToggleButton(qx.locale.Date.getDayName("wide", d));
        toggleButton.setAppearance("button-link");
        this.__pane.add(toggleButton, {row: d + 2, column: 0});

        // Add one checkbox per hour
        for (var h = 0; h < 24; h++) {
          var checkBox = new qx.ui.form.CheckBox();
          checkBox.setAllowGrowX(true);
          checkBox.setCenter(true);
          this.__pane.add(checkBox, {row: d + 2, column: h + 1});
          this.__togglers.push(checkBox);
          checkBox.addListener("changeValue", this.__updateValue, this);

          if (d === 0) {
            checkBox.setBackgroundColor("rgba(255, 10, 10, " + (h % 2 ? 0.15 : 0.1) + ")");
          }
          else {
            checkBox.setBackgroundColor("rgba(100, 100, 100, " + (h % 2 ? 0.1 : 0.0) + ")");
          }
        }

        // Bind toggler
        for (var x = 0; x < 24; x++) {
          toggleButton.bind("value", this.__togglers[x + (d * 24)], "value");
        }
      }
    },

    __createDayButtons : function() {
      for (var h = 0; h < 24; h++) {
        var toggleButton = new qx.ui.form.ToggleButton(h.toString());
        toggleButton.setAppearance("button-link");
        this.__pane.add(toggleButton, {row: 1, column: h + 1});

        for (var x = 0; x < 7; x++) {
          toggleButton.bind("value", this.__togglers[(x * 24) + h], "value");
        }
      }
    },

    /* This method updates the value-property and sends the "changeValue" 
     * event after a period of time, to tell the object-proxy that values have changed.
     *
     * This is a method which can be used as listener for value updates.
     * See "_createWidget" for details.
     * */
    _propertyUpdaterTimed: function(new_data){

      var timer = qx.util.TimerManager.getInstance();
      if(this.__propertyTimer != null){
        timer.stop(this.__propertyTimer);
        this.__propertyTimer = null;
      }
      this.__propertyTimer = timer.start(function(){
          timer.stop(this.__propertyTimer);
          this.__propertyTimer = null;
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
          bits += this.__togglers[(day*24)+hour].getValue() ? "1" : "0";
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
            this.__togglers[(day*24)+hour].setValue(value.getItem(0)[(day * 24) + hour] == 1);
          }
        }
      }
    }
  },

  destruct : function() {
    this.__gridLayout = null;
    this._disposeObjects("_pane");
  }
});
