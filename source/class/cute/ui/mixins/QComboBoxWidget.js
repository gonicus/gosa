qx.Mixin.define("cute.ui.mixins.QComboBoxWidget",
{
  members:
  {
    processQComboBoxWidget : function(loc, name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
      var widget = new cute.ui.widgets.QComboBoxWidget();

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

      this.processCommonProperties(name, widget, props);
      this._widgets[name] = widget;
      this.__add_widget_to_extension(name, loc);

      // Add listeners for value changes.
      widget.addListener("changeValue", function(e){
        this.set(realname, e.getData());
        this.setModified(true);
      }, this);

      return widget;
    }
  }
});
