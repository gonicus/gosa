qx.Mixin.define("cute.ui.mixins.QGraphicsViewWidget",
{
  members:
  {

    processQGraphicsViewWidget: function(loc, name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
      var widget = new cute.ui.widgets.QGraphicsViewWidget();
      this.processCommonProperties(widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);

      widget.addListener("changeValue", function(e){
          this.set(realname, e.getData());
          this.setModified(true);
        }, this);

      return widget;
    },

    /* Bind values from the remote-object to ourselves and vice-versa.
     * */
    processQGraphicsViewWidgetBinding: function(widgetName, propertyName){
      widgetName = widgetName.replace(/Edit$/, "");
      this._object.bind(propertyName, this, widgetName);
      this.bind(widgetName, this._object, propertyName);
    }
  }
});
