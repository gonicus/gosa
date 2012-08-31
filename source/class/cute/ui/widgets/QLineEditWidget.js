qx.Class.define("cute.ui.widgets.QLineEditWidget", {

  extend: cute.ui.widgets.MultiEditWidget,

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
 
    _default_value: "",

    /* Set a new value for the widget given by id.
     * */
    _setWidgetValue: function(id, value){
      try{
        this._getWidget(id).setValue(value);
      }catch(e){
        this.error("failed to set widget value for " + this.getAttribute() + ". "+ e);
      }
    },

    _setEchoMode: function(){
      this._current_length = 0;
      this.removeAll();
      this._widgetContainer = [];
      this._generateGui();
    },

    shortcutExecute : function()
    {
      this.focus();
    },

    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function(){
      var w;
      
      if(this.getEchoMode() == "password"){
        w = new qx.ui.form.PasswordField();
      }else{
        w = new qx.ui.form.TextField();
        w.getContentElement().setAttribute("spellcheck", true);
      }
      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }

      if(this.getMaxLength()){
        w.setMaxLength(this.getMaxLength());
      }

      w.setLiveUpdate(true);
      w.addListener("focusout", this._propertyUpdater, this); 
      w.addListener("changeValue", this._propertyUpdaterTimed, this); 
      this.bind("valid", w, "valid");
      this.bind("invalidMessage", w, "invalidMessage");
      return(w);
    }
  }
});
