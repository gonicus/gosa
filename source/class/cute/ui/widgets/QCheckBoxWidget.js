qx.Class.define("cute.ui.widgets.QCheckBoxWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    this._chkBoxWidget = new qx.ui.form.CheckBox();
    this.add(this._chkBoxWidget);
    this.bind("label", this._chkBoxWidget, "label");
  },

  properties: {

    /* Tells the widget how to display its contents
     * e.g. for mode 'password' show [***   ] only.
     * */
    label : {
      init : "",
      check : "String",
      event : "_labelChanged"
    }
  },

  members: {

    _chkBoxWidget: null,
    _property_timer: null,
    _was_manually_initialized: false,

    _getCleanValue: function(){
      this._chkBoxWidget.getValue();
    },

    /* Sends an update event for the current values of this widget.
     * e.g. not empty.
     * */
    _updateValues: function(){
      var ok = true;
      for(var i=1; i< this._widgets.length; i++){
        this._widgets[i].setValid(true);
        if(this._widgets[i].getValue() == ""){
          ok = false;
          this._widgets[i].setValid(false);
        }
      }
      if(ok){
        this.setModified(true);
        this.fireDataEvent("valueChanged", this._getCleanValue());
      }
    },

    /* Creates an update-function for each widget to ensure that values are set
     * after a given period of time.
     */
    __timedPropertyUpdater: function(id, userInput){
      var func = function(value){
        var timer = qx.util.TimerManager.getInstance();
        this.addState("modified");
        if(this._property_timer != null){
          timer.stop(this._property_timer);
          this._property_timer = null;
        }
        this._property_timer = timer.start(function(){
          this.removeState("modified");
          timer.stop(this._property_timer);
          this._property_timer = null;
          
          this.getValue().setItem(id, userInput.getValue());
          this._updateValues();
        }, null, this, null, 2000);
      }
      return func;
    },

    /* This method returns a function which directly updates the property-value.
     * */
    __propertyUpdater: function(id, userInput){
      var func = function(value){
        var timer = qx.util.TimerManager.getInstance();
        if(this._property_timer != null){
          timer.stop(this._property_timer);
          this._property_timer = null;
        }
        if(this.hasState("modified")){
          this.removeState("modified");
          this.getValue().setItem(id, userInput.getValue());
          this._updateValues();
        }
      }
      return func;
    },

    /* Apply method for the value property.
     * This method will regenerate the gui.
     * */
    _applyValue: function(value, old_value){

    },

    setInvalidMessage: function(message){
      this._chkBoxWidget.setInvalidMessage(message);
    },

    resetInvalidMessage: function(){
      this._chkBoxWidget.resetInvalidMessage();
    },

    focus: function(){
      this._chkBoxWidget.focus();
    },

    setValid: function(bool){
      this._chkBoxWidget.setValid(bool);
    }
  }
});
