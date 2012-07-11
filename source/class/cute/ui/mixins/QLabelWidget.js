qx.Mixin.define("cute.ui.mixins.QLabelWidget",
{
  members:
  {
    processQLabelWidget : function(name, props)
    {
      var label = new qx.ui.basic.Label(this.tr(this.getStringProperty('text', props)));
      this.processCommonProperties(label, props);

      this._widgets[name] = label;
      return label;
    }
  }
});
