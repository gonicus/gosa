qx.Mixin.define("cute.ui.mixins.QCheckBoxWidget",
{
  members:
  {

    processQCheckBoxWidget : function(loc, name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
      var widget = new cute.ui.widgets.QCheckBoxWidget();
      this.processCommonProperties(name, widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);

      if("text" in props){
        widget.setLabel(props["text"]["string"]);
      }

      widget.addListener("changeValue", function(e){
          this.set(realname, e.getData());
          this.setModified(true);
        }, this);

      return widget;
    }
  }
});
