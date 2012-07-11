qx.Mixin.define("cute.ui.mixins.QLineEditWidget",
{
  members:
  {

    processQLineEditWidget : function(name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
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
      this._object.bind(realname, this, realname);
      this.bind(realname, this._object, realname);

      // set widget properties
      widget.setMultivalue(this.getAttributes_()[realname]['multivalue']);

      // Add listeners for value changes.
      //widget.setLiveUpdate(true);
      widget.addListener("changedByTyping", this.__timedPropertyUpdater(realname, widget), this);
      widget.addListener("changedByFocus", this.__propertyUpdater(realname, widget), this);

      return widget;
    }
  }
});
