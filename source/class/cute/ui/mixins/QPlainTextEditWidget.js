qx.Mixin.define("cute.ui.mixins.QPlainTextEditWidget",
{
  members:
  {

    processQPlainTextEditWidget : function(name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
      var ad = this.getAttributeDefinitions_()[realname];
      if (!ad) {
        this.error("*** wired attribute '" + realname + "' does not exist in the object definition");
	return null
      }

      var widget = new cute.ui.widgets.QPlainTextEditWidget();
      
      // Set placeholder
      var placeholder = this.getStringProperty('placeholderText', props);
      if (placeholder != null) {
        widget.setPlaceholder(this.tr(placeholder));
      }

      // Set max length
      var ml = this.getNumberProperty('maxLength', props);
      if (ml != null) {
        widget.setMaxLength(ml);
      }

      this.processCommonProperties(widget, props);
      this._widgets[name] = widget;

      // set widget properties
      widget.setMultivalue(this.getAttributeDefinitions_()[realname]['multivalue']);

      // Add listeners for value changes.
      //widget.setLiveUpdate(true);
      //this.bind(realname, widget, "value");
      widget.addListener("valueChanged", function(e){
          this.set(realname, e.getData());
          this.setModified(true);
        }, this);

      return widget;
    },

    /* Bind values from the remote-object to ourselves and vice-versa.
     * */
    processQTextEditWidgetBinding: function(widgetName, propertyName){
      widgetName = widgetName.replace(/Edit$/, "");
      this._object.bind(propertyName, this, widgetName);
      this.bind(widgetName, this._object, propertyName);
    }
  }
});
