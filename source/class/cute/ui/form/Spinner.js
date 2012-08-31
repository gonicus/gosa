qx.Class.define("cute.ui.form.Spinner", {
  extend: qx.ui.form.Spinner,

  properties:{

    /** The value of the spinner. */
    value:
    {
      refine: true,
      init : null
    }
  },

  members: {

    /** Saved last value in case invalid text is entered */
    __lastValidValue_ : null,


    /**
     * Apply routine for the value property.
     *
     * It checks the min and max values, disables / enables the
     * buttons and handles the wrap around.
     *
     * @param value {Number} The new value of the spinner
     * @param old {Number} The former value of the spinner
     */
    _applyValue: function(value, old)
    {
      var textField = this.getChildControl("textfield");

      this._updateButtons();

      // save the last valid value of the spinner
      this.__lastValidValue_ = value;

      // write the value of the spinner to the textfield
      if (value !== null) {
        if (this.getNumberFormat()) {
          textField.setValue(this.getNumberFormat().format(value));
        } else {
          textField.setValue(value + "");
        }
      } else {
        textField.setValue("");
      }
    },

    /**
     * Apply routine for the numberFormat property.<br/>
     * When setting a number format, the display of the
     * value in the textfield will be changed immediately.
     *
     * @param value {Boolean} The new value of the numberFormat property
     * @param old {Boolean} The former value of the numberFormat property
     */
    _applyNumberFormat : function(value, old) {
      var textfield = this.getChildControl("textfield");
      textfield.setFilter(this._getFilterRegExp());

      this.getNumberFormat().addListener("changeNumberFormat",
        this._onChangeNumberFormat, this);

      this._applyValue(this.__lastValidValue_, undefined);
    },
    
    /**
     * Check whether the value being applied is allowed.
     *
     * If you override this to change the allowed type, you will also
     * want to override {@link #_applyValue}, {@link #_applyMinimum},
     * {@link #_applyMaximum}, {@link #_countUp}, {@link #_countDown}, and
     * {@link #_onTextChange} methods as those cater specifically to numeric
     * values.
     *
     * @param value {Any}
     *   The value being set
     * @return {Boolean}
     *   <i>true</i> if the value is allowed;
     *   <i>false> otherwise.
     */
    _checkValue : function(value) { 
      if(value == "" || value == null){
        return(true);
      }
      return typeof value === "number" && value >= this.getMinimum() && value <= this.getMaximum();
    },


    /**
     * Callback method for the "change" event of the textfield.
     *
     * @param e {qx.event.type.Event} text change event or blur event
     */
    _onTextChange : function(e)
    {
      var textField = this.getChildControl("textfield");
      var value = undefined;

      // if a number format is set
      if (this.getNumberFormat())
      {
        // try to parse the current number using the number format
        try {
          value = this.getNumberFormat().parse(textField.getValue());
        } catch(ex) {
          // otherwise, process further
        }
      }

      if(textField.getValue() == ""){
        this.setValue(null);
      }

      if (value === undefined)
      {
        // try to parse the number as a float
        value = parseFloat(textField.getValue());
      }

      // if the result is a number
      if (!isNaN(value))
      {
        // Fix range
        if (value > this.getMaximum()) {
          textField.setValue(this.getMaximum() + "");
          return;
        } else if (value < this.getMinimum()) {
          textField.setValue(this.getMinimum() + "");
          return;
        }

        // set the value in the spinner
        this.setValue(value);
      }
      else
      {
        // otherwise, reset the last valid value
        this._applyValue(this.__lastValidValue_, undefined);
      }
    }
  }
});
