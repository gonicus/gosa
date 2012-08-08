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
  
    _setEchoMode: function(){
      this._current_length = 0;
      this.removeAll();
      this._widgetContainer = [];
      this._generateGui();
    },

    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function(){

      if(this.getEchoMode() == "password"){
        var w = new qx.ui.form.PasswordField();
      }else{
        var w = new qx.ui.form.TextField();
      }
      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }

      w.setLiveUpdate(true);
      w.addListener("focusout", this._propertyUpdater, this); 
      w.addListener("changeValue", this._propertyUpdaterTimed, this); 
      return(w);
    }
  }
});
