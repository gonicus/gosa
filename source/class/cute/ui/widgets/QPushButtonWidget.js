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
qx.Class.define("cute.ui.widgets.QPushButtonWidget",
{
  extend : cute.ui.widgets.Widget,

  properties: {

    text : {
      init : "",
      check : "String",
      apply : "_setText",
      nullable: true
    }

  },

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
    this._widget = new qx.ui.form.Button();
    this.add(this._widget, {top:0, bottom:0, left:0, right: 0});
  },

  members :
  {
    _widget: null,

    _setText : function(value)
    {
      this._widget.setLabel(this.tr(value));
    },

    /* Apply collected gui properties to this widet
     * */
    _applyGuiProperties: function(props){
      if(props["text"] && props["text"]["string"]){
        this._setText(props["text"]["string"]);
      }
    }

  }
});

// vim:tabstop=2:expandtab:shiftwidth=2
