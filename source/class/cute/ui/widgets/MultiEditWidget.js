qx.Class.define("cute.ui.widgets.MultiEditWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this._widgetContainer = [];
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));
  },

  destruct : function(){
    this._property_timer = null;
    this._disposeArray("_widgetContainer");
  },

  members: {

    _widgetContainer: null,
    _property_timer: null,
    _current_length: 0,
    _skipUpdates: false,


    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function(){
      var w = new qx.ui.form.PasswordField("Dummy!");
      w.setLiveUpdate(true);
      w.addListener("focusout", this._propertyUpdater, this); 
      w.addListener("changeValue", this._propertyUpdaterTimed, this); 
      return(w);
    },

    _getCleanValues: function()
    {
      var data = new qx.data.Array();
      for(var i=0; i<this._current_length; i++){
        var val = this._getWidgetValue(i);
        if(val != null && val != ""){
          data.push(val);
        }
      }
      return(data);
    },

    _setWidgetValue: function(id, value){
      this._getWidget(id).setValue(value);
    },

    _getWidgetValue: function(id){
      return this._getWidget(id).getValue();
    },


    _propertyUpdater: function(){
      if(this._skipUpdates || !this.hasState("modified")){
        return;
      }
      for(var i=0; i< this._current_length; i++){
        this.getValue().setItem(i, this._getWidgetValue(i));
      }
      this.fireDataEvent("changeValue", this._getCleanValues());
      var timer = qx.util.TimerManager.getInstance();
      if(this._property_timer != null){
        timer.stop(this._property_timer);
        this._property_timer = null;
        this.removeState("modified");
      }
    },

    _propertyUpdaterTimed: function(){
      if(this._skipUpdates){
        return;
      }

      this.addState("modified");
      for(var i=0; i< this._current_length; i++){
        this.getValue().setItem(i, this._getWidgetValue(i));
      }
      var timer = qx.util.TimerManager.getInstance();
      if(this._property_timer != null){
        timer.stop(this._property_timer);
        this._property_timer = null;
      }
      this._property_timer = timer.start(function(){
          this.removeState("modified");
          timer.stop(this._property_timer);
          this._property_timer = null;
          this.fireDataEvent("changeValue", this._getCleanValues());
        }, null, this, null, 2000);
    },

    _getWidget: function(id){
      return(this._widgetContainer[id].getWidget());
    },

    _addWidget: function(id){
      if(!(id in this._widgetContainer)){
        var w = this._createWidget(id);
        var c = new cute.ui.widgets.MultiEditContainer(w);
        this._widgetContainer[id] = c;
        c.addListener("add", function(){
          this._skipUpdates = true;
          this.getValue().push(null);
          this._skipUpdates = true;
          this._generateGui();
        }, this);
        c.addListener("delete", function(){
          this._skipUpdates = true;
          this.getValue().splice(id, 1);
          this._skipUpdates = false;
          this._generateGui();
        }, this);
      }
      this.add(this._widgetContainer[id]);
    },

    _delWidget: function(id){
      this.remove(this._widgetContainer[id]);
    },

    _generateGui: function(){
      this._skipUpdates = true;

      // Calcute length of visible widgets
      var length = this.getValue().getLength();
      if(!length){
        this.getValue().push(null);
        length = 1;
      }

      if(!this.isMultivalue()){
        length = 1;
      }

      var last_length = this._current_length;
      this._current_length = length;

      for(var i=0; i<length; i++){
        this._addWidget(i);
        this._setWidgetValue(i, this.getValue().getItem(i));
        if(length > 1){
          this._widgetContainer[i].setHasDelete(true);
          this._widgetContainer[i].setHasAdd(i == length -1);
        }else{
          if(this.isMultivalue()){
            this._widgetContainer[i].setHasAdd(true);
            this._widgetContainer[i].setHasDelete(false);
          }else{
            this._widgetContainer[i].setHasAdd(false);
            this._widgetContainer[i].setHasDelete(false);
          }
        }
      }

      // Remove all non-visible widgets
      for(var l=length; l<last_length; l++){
        this._delWidget(l);
      }
      this._skipUpdates = false;
    },

    /* Apply method for the value property.
     * This method will regenerate the gui.
     * */
    _applyValue: function(value, old_value){
      if(!value.getLength()){
        value.push(null);
      }
      this._generateGui();
    },

    /* This is the apply method for the multivalue-flag
     * If the multivalue flag is changed, the gui will be regenerated.
     * */
    _applyMultivalue: function(){
      this._generateGui();
    },

    _applyRequired: function(bool){
      this._generateGui();
    },

    setInvalidMessage: function(message){
      for(var i=0; i < this._current_length; i++){
        this._widgetContainer[i].getWidget().setInvalidMessage(message);
      }
    },

    resetInvalidMessage: function(){
      for(var i=0; i < this._current_length; i++){
        this._widgetContainer[i].getWidget().resetInvalidMessage();
      }
    },

    focus: function(){
      for(var i=0; i < this._current_length; i++){
        this._widgetContainer[i].getWidget().focus();
      }
    },

    setValid: function(bool){
      for(var i=0; i < this._current_length; i++){
        this._widgetContainer[i].getWidget().setValid(bool);
        console.log(this._widgetContainer[i].getWidget().classname);
      }
    }
  }
});
