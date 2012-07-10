qx.Mixin.define("cute.ui.mixins.QLabelWidget",
{
  members:
  {
    processQLabelWidget : function(name, props)
    {
      var label = new qx.ui.basic.Label(this.getStringProperty('text', props));

      // Set tooltip
      if (this.getStringProperty('toolTip', props)) {
        label.setToolTip(new qx.ui.tooltip.ToolTip(this.getStringProperty('toolTip', props)));
      }

      this.processCommonProperties(label, props);

      this._widgets[name] = label;
      return label;
    }
  }
});
