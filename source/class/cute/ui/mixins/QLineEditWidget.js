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
        widget.setPlaceholder(this.tr(placeholder));
      }

      // Set max length
      var ml = this.getNumberProperty('maxLength', props);
      if (ml != null) {
        widget.setMaxLength(ml);
      }

      this.processCommonProperties(widget, props);
      this._widgets[name] = widget;

      // set widget properties
      widget.setMultivalue(this.getAttributeDefinitions_()[realname]['multivalue']);

      // Bind values from the remote-object to ourselves and vice-versa.
      this._object.bind(realname, this, realname);
      this.bind(realname, this._object, realname);

      // Add listeners for value changes.
      //widget.setLiveUpdate(true);
      //this.bind(realname, widget, "value");
      widget.addListener("valueChanged", function(e){
          this.set(realname, e.getData());
        }, this);

      return widget;
    }
  }
});
