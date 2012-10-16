/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.widgets.MultiEditWidget", {

  extend: gosa.ui.widgets.Widget,

  construct: function(){
    this._widgetContainer = [];
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));

    this.setFocusable(true);

    // Generate the gui
    this._generateGui();
  },

  destruct : function(){

    this._property_timer = null;
    this._disposeArray("_widgetContainer");

    // Remove all listeners and then set our values to null.
    qx.event.Registration.removeAllListeners(this); 

    this.setBuddyOf(null);
    this.setGuiProperties(null);
    this.setValues(null);
    this.setValue(null);
    this.setBlockedBy(null);
  },

  members: {

    _ready: false,
    _default_value: null,
    _widgetContainer: null,
    _property_timer: null,
    _current_length: 0,
    _skipUpdates: false,

    _initComplete: function(){
      this._generateGui();
    },

    /* Sets an error message for this widgets
     * */
    setErrorMessage: function(message, id){
      var w = this._getWidget(id);
      w.setInvalidMessage(message);
      w.setValid(false);
    },


    /* Resets the "invalidMessage" string for all widgets.
     * */
    resetErrorMessage: function(){
      for(var i=0; i < this._current_length; i++){
        this._getWidget(i).resetInvalidMessage();
        this._getWidget(i).setValid(true);
      }
    },


    /* Mark the given widget as required
     * */
    _markAsRequired: function(widget){
      widget.setBackgroundColor("mandatory");    
    },


    /* Returns the value from the widget given by its id
     * */
    _getWidgetValue: function(id){
      return this._getWidget(id).getValue();
    },


    /* Removes the widget from the view-port
     * */
    __delWidget: function(id){
      this.remove(this._widgetContainer[id]);
    },

   
    /* Returns the "real" widget (e.g. the qx.ui.form.Textfield)
     * For the given id.
     * */
    _getWidget: function(id){
      return(this._widgetContainer[id].getWidget());
    },


    /* Set a new value for the widget given by id.
     * */
    _setWidgetValue: function(id, value){
      try{
        this._getWidget(id).setValue(value);
      }catch(e){
        this.error("failed to set widget value for " + this.getAttribute() + ". "+ e);
      }
    },


    /* Create the "real"-widget element.
     * and connect it to the update methods
     * */
    _createWidget: function(){
      var w = new qx.ui.form.TextField();
      w.setLiveUpdate(true);
      w.addListener("focusout", this._propertyUpdater, this); 
      w.addListener("changeValue", this._propertyUpdaterTimed, this); 
      return(w);
    },


    /* Returns the widget values in a clean way,
     * to avoid saving null or empty values for an object
     * property.
     * */
    _getCleanValues: function()
    {
      var data = new qx.data.Array();
      for(var i=0; i<this._current_length; i++){
        var val = this._getWidgetValue(i);
        if(val !== null && val !== this._default_value){
          data.push(val);
        }
      }
      return(data);
    },


    /* Apply method for the value property.
     * */
    _applyValue: function(value, old_value){

      // This happens when we destroy this widget
      if(value === null){
        return;
      }

      // Ensure that at least one element is given.
      if(!value.getLength()){
        value.push(this._default_value);
      }
    },


    /* This is the apply method for the multivalue-flag
     * */
    _applyMultivalue: function(){
    },


    /* Sets the "focus" to the first input widgets
     * */
    focus: function(){
      if(this._widgetContainer.length){
        this._widgetContainer[0].getWidget().focus();
      }
    },


    /* This method updates the value-property and immediately 
     * sends the "changeValue" to tell the object-proxy that values have changed.
     *
     * This is a method which can be used as listener for value updates.
     * See "_createWidget" for details.
     * */
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


    /* This method updates the value-property and sends the "changeValue" 
     * event after a period of time, to tell the object-proxy that values have changed.
     *
     * This is a method which can be used as listener for value updates.
     * See "_createWidget" for details.
     * */
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


    /* Add a new widget to the view-port.
     * E.g. in multiedit this is used to show a new input line
     * after somebody clicked on the '+' button.
     * */
    _addWidget: function(id){
      if(!(id in this._widgetContainer)){
        var w = this._createWidget(id);

        // Mark widget as required
        if(this.getMandatory()){
          this._markAsRequired(w);
        }

        var c = new gosa.ui.widgets.MultiEditContainer(w);
        this._widgetContainer[id] = c;
        c.addListener("add", function(){
          this._skipUpdates = true;
          this.getValue().push(this._default_value);
          this._skipUpdates = true;
          this._generateGui();
        }, this);
        c.addListener("delete", function(){
          this._skipUpdates = true;
          this.getValue().splice(id, 1);
          this._skipUpdates = false;
          this._generateGui();
          this.addState("modified");
          this._propertyUpdater();
        }, this);
        this.add(this._widgetContainer[id]);
      }

      if(this.isMandatory()){
        this._markAsRequired(this._getWidget(id));
      }

      // Set the tabstop-index
      if(id < 20){
        this._getWidget(id).setTabIndex(this.getTabStopIndex() + id);
      }
    },


    /* Regenerates the view-port of this plugin.
     * It hides or shows only the required amount of widgets.
     * All not needed widgets will be excluded from the viewport.
     * */
    _generateGui: function(){

      // Do not forward events for input modifications while regenerating the gui
      this._skipUpdates = true;

      // Calculate length of visible widgets
      var length = this.getValue().getLength();
      if(!length){
        this.getValue().push(this._default_value);
        length = 1;
      }

      // Ensure that we have exactly one line for single value elements
      if(!this.isMultivalue()){
        length = 1;
      }

      // Remember the amount of shown widgets
      var last_length = this._current_length;
      this._current_length = length;

      // Add the required amount of widgets to the view-port and
      // set +/- buttons visibility.
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
        this.__delWidget(l);
      }

      // Forward uopdates again
      this._skipUpdates = false;
    }
  }
});
