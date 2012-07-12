qx.Mixin.define("cute.ui.mixins.QComboBoxWidget",
{
  members:
  {
    processQComboBoxWidget : function(name, props)
    {
      var widget;
      var editable = this.getBoolProperty('editable', props);
      var values = new qx.data.Array(this.getAttributeDefinitions_()[name.slice(0, name.length - 4)]['values']);
      values.sort();

      if (editable) {
        widget = new qx.ui.form.VirtualComboBox(values);
      } else {
        widget = new qx.ui.form.VirtualSelectBox(values);
      }

      this.processCommonProperties(widget, props);

      this._widgets[name] = widget;
      return widget;
    }
  }
});
