/* ************************************************************************

   Copyright: Cajus Pollmeier <pollmeier@gonicus.de>

   License:

   Authors:

 ************************************************************************ */

/* ************************************************************************

#asset(cute/*)

 ************************************************************************ */

/**
 * This is the main application class of your custom application "cute"
 */
qx.Class.define("cute.ui.widgets.Label",
{
  extend : qx.ui.basic.Label,

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  construct : function(text)
  {
    var target_text = text;

    // Extract potential key bindings from label text
    var regex = /^(.*)(&(.))(.*$)/g;
    var match = regex.exec(text);
    this._command = null;

    if (match) {
      target_text = match[1] + "<u>" + match[3] + "</u>" + (match.length == 5 ? match[4] : "");
      this._command = match[3];
    }

    // Call super class
    this._text = target_text;
    this.base(arguments, target_text);
    this.setRich(true);
  },

  properties :
  {
    mandatory : {
	  init: false,
      check: "Boolean",
      apply: "__applyMandatory"
    }
  },

  members :
  {

    /* Applies the mandatory state for this widget
     * */
    __applyMandatory: function(mandatory){
      if (mandatory) {
        this.setValue(this._text + "&nbsp;<b>*</b>");
      } else {
        this.setValue(this._text);
      }
    },

    getCommand: function() {
      return this._command;
    }
  }
});

/* vim:tabstop=2:expandtab:shiftwidth=2 */
