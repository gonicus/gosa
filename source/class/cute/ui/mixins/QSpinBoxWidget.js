qx.Mixin.define("cute.ui.mixins.QSpinBoxWidget",
{
  members:
  {

    processQSpinBoxWidget : function(loc, name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
      var ad = this.getAttributeDefinitions_()[realname];
      if (!ad) {
        this.error("*** wired attribute '" + realname + "' does not exist in the object definition");
	return null;
      }

      var widget = new qx.ui.form.Spinner();
      
      this.processCommonProperties(widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);

      // Add listeners for value changes.
      widget.addListener("changeValue", function(e){
          this.set(realname, e.getData());
          this.setModified(true);
        }, this);

      return widget;
    },

    /* Bind values from the remote-object to ourselves and vice-versa.
     * */
    processQSpinBoxWidgetBinding: function(widgetName, propertyName){
      widgetName = widgetName.replace(/Edit$/, "");
      this._object.bind(propertyName, this, widgetName);
      this.bind(widgetName, this._object, propertyName);
    }
  }
});
