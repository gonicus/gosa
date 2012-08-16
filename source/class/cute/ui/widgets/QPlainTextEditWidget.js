qx.Class.define("cute.ui.widgets.QPlainTextEditWidget", {

  extend: cute.ui.widgets.MultiEditWidget,

  members: {
 
    _default_value: "",

    /* Creates an input-widget depending on the echo mode (normal/password)
     * and connects the update listeners
     * */
    _createWidget: function(){
      var w = new qx.ui.form.TextArea();
      if(this.getPlaceholder()){
        w.setPlaceholder(this.getPlaceholder());
      }

      if(this.getMaxLength()){
        w.setMaxLength(this.getMaxLength());
      }

      w.setLiveUpdate(true);
      w.addListener("focusout", this._propertyUpdater, this);
      w.addListener("changeValue", this._propertyUpdaterTimed, this);
      w.getContentElement().setAttribute("spellcheck", true);
      return(w);
    }
  }
});
