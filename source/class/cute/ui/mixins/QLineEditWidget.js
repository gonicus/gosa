qx.Mixin.define("cute.ui.mixins.QLineEditWidget",
{
  members:
  {

    processQLineEditWidget : function(name, props)
    {
      var widget;

      // Set echo mode
      var echomode = this.getEnumProperty('echoMode', props);
      if (echomode == "QLineEdit::Password") {
        widget = new qx.ui.form.PasswordField();
      } else if (echomode == "QLineEdit::NoEcho") {
        this.error("*** TextField NoEcho not supported!");
        return null;
      } else if (echomode == "QLineEdit::PasswordEchoOnEdit") {
        this.error("*** TextField NoEcho not supported!");
        return null;
      } else {
        widget = new qx.ui.form.TextField();
      }

      // Set placeholder
      var placeholder = this.getStringProperty('placeholderText', props);
      if (placeholder != null) {
        widget.setPlaceholder(placeholder);
      }

      // Set max length
      var ml = this.getNumberProperty('maxLength', props);
      if (ml != null) {
        widget.setMaxLength(ml);
      }

      this.processCommonProperties(widget, props);
      this._widgets[name] = widget;

      // Bind values from the remote-object to ourselves and vice-versa.
      var realname = name.replace(/Edit$/, '', name);
      this._object.bind(realname, this, realname);
      this.bind(realname, this._object, realname);

      // Add listeners for value changes.
      widget.setLiveUpdate(true);
      widget.addListener("changeValue", this.__timedPropertyUpdater(realname, widget), this);
      widget.addListener("focusout", this.__propertyUpdater(realname, widget), this);

      return widget;
    }
  }
});
