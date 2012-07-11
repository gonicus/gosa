qx.Class.define("cute.ui.widgets.QLineEditWidget", {

  extend: cute.ui.widgets.Widget,

  construct: function(){
    this.base(arguments);  
    this._widgets = [];
    this._widgetContainer = [];
    this.setLayout(new qx.ui.layout.VBox(5));
  },

  properties: {
    echoMode : {
      init : "normal",
      nullable: true
    }
  },

  members: {
    _widgets: null,
    _widgetContainer: null,

    __getDel: function(id){
      var func = function(){
        var value = this.getValue().splice(id, 1);
        this.fireEvent("changedByTyping");
        this._resetFields();
        this.updateFields();
      }
      return func;
    },

    __updateValue: function(id, widget){
      var func = function(){
        var value = this.getValue();
        value.setItem(id, widget.getValue());
        this.fireEvent("changedByTyping");
      }
      return func;
    },

    getWidget: function(id){
      var w = new qx.ui.form.TextField("" + this.getValue().getItem(id));
      w.addListener("focusout", function(){
        this.fireEvent("changedByFocus");
      }, this);
      w.setLiveUpdate(true);
      w.addListener("changeValue", this.__updateValue(id, w), this); 
      return(w);
    },

    updateFields: function(){

      // Walk through values and create input fields for them
      var len = this.getValue().getLength();
      if(!this.isMultivalue()){
        len = 1;
      }

      for(var i=0; i< len; i++){

        // First check if we already have an widget for this position
        if(!(i in this._widgets)){
          var widget = this.getWidget(i);
          var container = new qx.ui.container.Composite(new qx.ui.layout.HBox(1));
          container.add(widget, {flex:1});
          this.add(container);

          if(this.isMultivalue()){
            var del = new qx.ui.form.Button("-");
            del.addListener('click', this.__getDel(i), this);
            container.add(del);

            // If its the last field, the add a '+' button 
            if(i == len-1){
              var add = new qx.ui.form.Button("+");
              add.addListener('click', function(){
                this._resetFields();
                this.getValue().push("");
                this.updateFields();
              }, this);
              container.add(add);
            }
          }
          this._widgets[i] = widget;
          this._widgetContainer[i] = container;
        }
      }

      // Remove Eventually left widgets.
      for(var e=this._widgets.length; e > this.getValue().getLength(); e++){
        this._widgets.splice(e, 1);
        this._widgetContainer.splice(e, 1);
      }
    },

    /* Apply method for the value property.
     * This method will regenerate the gui.
     * */
    _applyValue: function(value, old_value){

      // Ensure that we've at least one value here...
      if(!value.getLength()){
        value.push("");
      }

      if(old_value && old_value.getLength() != value.getLength()){
        this._resetFields();
      }

      this.updateFields();
    },

    /* This is the apply method for the multivalue-flag
     * If the multivalue flag is changed, the gui will be regenerated.
     * */
    _applyMultivalue: function(value){

      // Regenerate gui
      this._resetFields();
      this.updateFields();
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
