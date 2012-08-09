qx.Mixin.define("cute.ui.mixins.QGraphicsViewWidget",
{
  members:
  {

    processQGraphicsViewWidget: function(loc, name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
      var widget = new cute.ui.widgets.QGraphicsViewWidget();
      this.processCommonProperties(name, widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);

      widget.addListener("changeValue", function(e){
          this.set(realname, e.getData());
          this.setModified(true);
        }, this);

      return widget;
    }
  }
});
