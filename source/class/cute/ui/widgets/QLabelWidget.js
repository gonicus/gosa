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
qx.Class.define("cute.ui.widgets.QLabelWidget",
{
  extend : cute.ui.widgets.Widget,

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
      if(props["text"] && props["text"]["string"]){
        var text = props["text"]["string"];

        // Extract potential key bindings from label text
        var regex = /^(.*)(&(.))(.*$)/g;
        var match = regex.exec(this.tr(text));
        this._command = null;

        if (match) {
          text = match[1] + "<u>" + match[3] + "</u>" + (match.length == 5 ? match[4] : "");
          this._command = match[3];
          this._widget.setValue(text);
        } else {
          text = this.tr(text);
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
