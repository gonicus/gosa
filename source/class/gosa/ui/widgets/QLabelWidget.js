/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/* ************************************************************************

#asset(gosa/*)

 ************************************************************************ */

/**
 * This is the main application class of your custom application "gosa"
 */
qx.Class.define("gosa.ui.widgets.QLabelWidget",
{
  extend : gosa.ui.widgets.Widget,

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  construct : function()
  {
    this.base(arguments);

    // Call super class
    this.setLayout(new qx.ui.layout.Canvas());
    this._widget = new qx.ui.basic.Label();
    this._widget.setRich(true);
    this.add(this._widget, {top:0, bottom:0, left:0, right: 0});
    this.removeState("gosaInput");
  },

  destruct : function(){
    this._disposeObjects("_widget");

    // Remove all listeners and then set our values to null.
    qx.event.Registration.removeAllListeners(this); 

    this.setBuddyOf(null);
    this.setGuiProperties(null);
    this.setValues(null);
    this.setValue(null);
    this.setBlockedBy(null);
  },

  members :
  {
    _widget: null,
    _text: "",

    getText: function(){
      return(this._text);
    },

    setBuddy: function(w){
      this._widget.setBuddy(w);
    },


    /* Apply collected gui properties to this widet
     * */
    _applyGuiProperties: function(props){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(!props){
        return;
      }

      if(props["text"] && props["text"]["string"]){
        var text = props["text"]["string"];

        // Extract potential key bindings from label text
        var regex = /^(.*)(&(.))(.*$)/g;
        var match = regex.exec(this['tr'](text));
        this._command = null;

        if (match) {
          text = match[1] + "<u>" + match[3] + "</u>" + (match.length == 5 ? match[4] : "");
          this._command = match[3];
          this._widget.setValue(text);
        } else {
          text = this['tr'](text);
          this._widget.setValue(text);
        }
        this._text = text;
      }
    },


    /* Applies the mandatory state for this widget
     * */
    _applyMandatory: function(mandatory){
      if (mandatory) {
        this._widget.setValue(this._text + " <span style='color:red'>*</span> ");
      } else {
        this._widget.setValue(this._text);
      }
    },

    getCommand: function() {
      return this._command;
    }
  }
});

// vim:tabstop=2:expandtab:shiftwidth=2
