qx.Mixin.define("cute.ui.mixins.QLineEditWidget",
{
  members:
  {

    processQLineEditWidget : function(loc, name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
      var ad = this.getAttributeDefinitions_()[realname];
      if (!ad) {
        this.error("*** wired attribute '" + realname + "' does not exist in the object definition");
        return null;
      }

      var widget = new cute.ui.widgets.QLineEditWidget();

      // Set echo mode
      var echomode = this.getEnumProperty('echoMode', props);
      if (echomode == "QLineEdit::Password") {
        widget.setEchoMode('password');
      } else if (echomode == "QLineEdit::NoEcho") {
        this.error("*** TextField NoEcho not supported!");
        return null;
      } else if (echomode == "QLineEdit::PasswordEchoOnEdit") {
        this.error("*** TextField NoEcho not supported!");
        return null;
      }

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

      // set widget properties
      widget.setMultivalue(this.getAttributeDefinitions_()[realname]['multivalue']);

      // Add listeners for value changes.
      //widget.setLiveUpdate(true);
      widget.addListener("changeValue", function(e){
          this.set(realname, e.getData());
          this.setModified(true);
        }, this);

      return widget;
    }
  }
});
