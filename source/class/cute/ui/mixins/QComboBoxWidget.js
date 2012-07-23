qx.Mixin.define("cute.ui.mixins.QComboBoxWidget",
{
  members:
  {
    processQComboBoxWidget : function(name, props)
    {


      console.log(name, props);

      var realname = name.replace(/Edit$/, '', name);
      var widget = new cute.ui.widgets.QComboBoxWidget();
      
      var editable = this.getBoolProperty('editable', props);
      var values = new qx.data.Array(this.getAttributeDefinitions_()[name.slice(0, name.length - 4)]['values']);
      values.sort();

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
      widget.setEditable(editable);
      widget.setValues(values);

      // Add listeners for value changes.
      //widget.setLiveUpdate(true);
      //this.bind(realname, widget, "value");
      widget.addListener("valueChanged", function(e){
          this.set(realname, e.getData());
          this.setModified(true);
        }, this);

      return widget;
    },

    /* Bind values from the remote-object to ourselves and vice-versa.
     * */
    processQComboBoxWidgetBinding: function(widgetName, propertyName){
      widgetName = widgetName.replace(/Edit$/, "");
      this._object.bind(propertyName, this, widgetName);
      this.bind(widgetName, this._object, propertyName);
    }
  }
});
