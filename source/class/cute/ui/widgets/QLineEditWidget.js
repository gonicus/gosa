qx.Class.define("cute.ui.widgets.QLineEditWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this._widgets = [];
    this._widgetContainer = [];
    this.base(arguments);  
    this.setLayout(new qx.ui.layout.VBox(5));
  },

  properties: {

    /* Tells the widget how to display its contents
     * e.g. for mode 'password' show [***   ] only.
     * */
    echoMode : {
      init : "normal",
      check : ["normal", "password"],
      apply : "_setEchoMode",
      nullable: true
    }
  },

  members: {

    _widgets: null,
    _widgetContainer: null,
    _property_timer: null,

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
          this.fireEvent("valueChanged");
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
          this.fireEvent("valueChanged");
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
        this.fireEvent("valueChanged");
      }
      return func;
    },

    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    __getWidget: function(id){
      if(this.getEchoMode() == "password"){
        var w = new qx.ui.form.PasswordField("" + this.getValue().getItem(id));
      }else{
        var w = new qx.ui.form.TextField("" + this.getValue().getItem(id));
      }
      w.setLiveUpdate(true);
      w.addListener("focusout", this.__propertyUpdater(id, w), this); 
      w.addListener("changeValue", this.__timedPropertyUpdater(id, w), this); 
      return(w);
    },

    _generateGui: function(){

      // Walk through values and create input fields for them
      var len = this.getValue().getLength();
      for(var i=0; i< len; i++){

        // First check if we already have an widget for this position
        if(!(i in this._widgets)){
          var widget = this.__getWidget(i);
          var container = new qx.ui.container.Composite(new qx.ui.layout.HBox(1));
          container.add(widget, {flex:1});
          this.add(container);

          if(this.isMultivalue()){

            // Add delete button for input fields, except the first.
            if(i > 0){
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
      }
    },

    /* Apply method for the value property.
     * This method will regenerate the gui.
     * */
    _applyValue: function(value, old_value){

      if(old_value && old_value.getLength() != value.getLength()){
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

    /* Sets the echo-mode of the text-field.
     * E.g. in password mode only * are shown instead of the real content.
     * */
    _setEchoMode: function(){
    
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
    }
  }
});
