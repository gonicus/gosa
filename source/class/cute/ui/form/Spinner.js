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
      var value;

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
        this._applyValue(this.__lastValidValue, undefined);
      }
    }
  }
});
