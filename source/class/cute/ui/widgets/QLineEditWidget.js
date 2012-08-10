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
 
    default_value: "",


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

      if(this.getEchoMode() == "password"){
        var w = new qx.ui.form.PasswordField();
      }else{
        var w = new qx.ui.form.TextField();
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
      return(w);
    }
  }
});
