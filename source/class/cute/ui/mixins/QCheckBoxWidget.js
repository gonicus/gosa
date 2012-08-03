qx.Mixin.define("cute.ui.mixins.QCheckBoxWidget",
{
  members:
  {

    processQCheckBoxWidget : function(loc, name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
      var widget = new cute.ui.widgets.QCheckBoxWidget();
      this.processCommonProperties(widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);

      if("text" in props){
        widget.setLabel(props["text"]["string"]);
      }

      widget.addListener("valueChanged", function(e){
          this.set(realname, e.getData());
          this.setModified(true);
        }, this);

      return widget;
    },

    /* Bind values from the remote-object to ourselves and vice-versa.
     * */
    processQCheckBoxWidgetBinding: function(widgetName, propertyName){
      widgetName = widgetName.replace(/Edit$/, "");
      this._object.bind(propertyName, this, widgetName);
      this.bind(widgetName, this._object, propertyName);
    }
  }
});
