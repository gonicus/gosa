qx.Class.define("cute.ui.widgets.QSpinBoxWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this._widgets = [];
    this._widgetContainer = [];
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));
  },

  destruct : function(){
    this._property_timer = null;
    this._disposeArray("_widgets");
    this._disposeArray("_widgetContainer");
  },

  members: {

    _widgets: null,
    _widgetContainer: null,
    _property_timer: null,
    _was_manually_initialized: false,

    _getCleanValue: function(){

      var res = new qx.data.Array();

      // No values given, return null
      if(!this.getValue().getLength()){
        return(res);
      }

      // A single value is given but its empty.
      if(this.getValue().getLength() == 1 && this.getValue().getItem(0) == ""){
        return(res);
      }

      // Append all non empty values
      for(var i=0; i<this.getValue().getLength(); i++){
        var v = this.getValue().getItem(i);
        if(v != ""){
          res.push(v);
        }
      }
      return(res);
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

    /* Returns a a delete-callback method
     * */
    __getDel: function(id){
      var func = function(){
        this.getValue().splice(id, 1);
        this._resetFields();
        this._generateGui();
        this._updateValues();
      }
      return func;
    },

    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    __getWidget: function(id){

      // Create a copy of the current value and check if we've
      // got at least one value, if not then add a dumy one.
      var value = this.getValue().getItem(id);
      if(value == null){
        value = 0;
      }
      var w = new cute.ui.form.Spinner();
      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }
      //w.addListener("focusout", this.__propertyUpdater(id, w), this); 
      w.addListener("changeValue", this.__timedPropertyUpdater(id, w), this); 
      return(w);
    },

    _generateGui: function(){

      // Walk through values and create input fields for them
      var values = this.getValue();
      var len = values.getLength();
      for(var i=0; i< len; i++){

        // First check if we already have an widget for this position
        if(!(i in this._widgets)){
          var widget = this.__getWidget(i);
          var container = new qx.ui.container.Composite(new qx.ui.layout.HBox(1));
          container.add(widget, {flex:1});
          this.add(container);

          if(this.isMultivalue()){

            // Add delete button for input fields, except the first.
            if(len > 1){
              var del = new qx.ui.form.Button("-");
              del.addListener('click', this.__getDel(i), this);
              container.add(del);
            }

            // If its the last field, the add a '+' button 
            if(i == len-1){
              var add = new qx.ui.form.Button("+");
              add.addListener('click', function(){
                this._resetFields();
                this.getValue().push("");
                this._generateGui();
              }, this);
              container.add(add);
            }
          }
          this._widgets[i] = widget;
          this._widgetContainer[i] = container;
        }
        //if(i < this.getValue().getLength()){
        //  var value = this.getValue().getItem(i);
        //  this._widgets[i].setValue(value);
        //}
      }
    },

    /* Apply method for the value property.
     * This method will regenerate the gui.
     * */
    _applyValue: function(value, old_value){

      // Ensure that we've at least one value
      if(!value.getLength()){
        this._was_manually_initialized = true;
        value.push(null);
      }
      if(this._was_manually_initialized || old_value && old_value.getLength() != value.getLength()){
        this._resetFields();
      }
      this._generateGui();
    },

    /* This is the apply method for the multivalue-flag
     * If the multivalue flag is changed, the gui will be regenerated.
     * */
    _applyMultivalue: function(){

      // Regenerate gui
      this._resetFields();
      this._generateGui();
    },

    /* Remove all sub-widgets added to the container and clear
     * the list containing references to those objects.
     * */
    _resetFields: function(){
      for(var item in this._widgetContainer){
        this.remove(this._widgetContainer[item]);
      }
      this._widgets = [];
      this._widgetContainer = [];
    },

    setInvalidMessage: function(message){
      for(var i=0; i < this._widgets.length; i++){
        this._widgets[i].setInvalidMessage(message);
      }
    },

    resetInvalidMessage: function(){
      for(var i=0; i < this._widgets.length; i++){
        this._widgets[i].resetInvalidMessage();
      }
    },

    focus: function(){
      if(this._widgets.length){
        this._widgets[0].focus();
      }
    },

    setValid: function(bool){
      for(var i=0; i < this._widgets.length; i++){
        this._widgets[i].setValid(bool);
      }
    }
  }
});
