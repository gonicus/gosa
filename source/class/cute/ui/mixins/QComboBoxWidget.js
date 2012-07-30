qx.Mixin.define("cute.ui.mixins.QComboBoxWidget",
{
  members:
  {
    processQComboBoxWidget : function(name, props)
    {
      var realname = name.replace(/Edit$/, '', name);
      var widget = new cute.ui.widgets.QComboBoxWidget();
      
      var ad = this.getAttributeDefinitions_()[realname];
      if (!ad) {
        this.error("*** wired attribute '" + realname + "' does not exist in the object definition");
        return null;
      }

      var values = new qx.data.Array;
      if (ad['values']) {
        var items = [];

	if (ad['mandatory'] === undefined || ad['mandatory'] !== true) {
            var item = new cute.data.model.SelectBoxItem();
	    item.setValue("");
	    item.setKey(null);
            items.push(item);
	}

        if (qx.Bootstrap.getClass(ad['values']) == "Object") {

          for (var k in ad['values']) {
            var item = new cute.data.model.SelectBoxItem();
            item.setKey(k);
	    if (ad['values'][k]['value']) {
              item.setValue(ad['values'][k]['value']);
              item.setIcon(ad['values'][k]['icon']);
	    } else {
              item.setValue(ad['values'][k]);
	    }
            items.push(item);
          }

        } else {

          for (var k = 0; k < ad['values'].length; k++) {
            var item = new cute.data.model.SelectBoxItem();
            item.setValue(ad['values'][k]);
            item.setKey(ad['values'][k]);
            items.push(item);
          }

        }

        values = new qx.data.Array(items);
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
      widget.setMultivalue(ad['multivalue']);
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
