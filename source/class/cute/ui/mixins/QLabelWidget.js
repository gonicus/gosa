qx.Mixin.define("cute.ui.mixins.QLabelWidget",
{
  members:
  {
    processQLabelWidget : function(loc, name, props)
    {
      var label = new cute.ui.widgets.Label(this.tr(this.getStringProperty('text', props)));
      this.processCommonProperties(name, label, props);

      this._widgets[name] = label;
      this.__add_widget_to_extension(name, loc);

      return label;
    }
  }
});
