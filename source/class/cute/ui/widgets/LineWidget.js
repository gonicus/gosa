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
qx.Class.define("cute.ui.widgets.LineWidget",
{
  extend : cute.ui.widgets.Widget,

  properties: {

    orientation : {
      init : "Qt::Horizontal",
      check : ["Qt::Horizontal", "Qt::Vertical"],
      apply : "_setOrientation",
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
    this._widget = new qx.ui.core.Widget();
    this.add(this._widget, {top:0, bottom:0, left:0, right: 0});

    this._setOrientation("Qt::Horizontal");
    this.removeState("cuteInput");
  },

  members :
  {
    _widget: null,

    _setOrientation : function(value)
    {
      if("Qt::Horizontal") {
        this._widget.setDecorator("separator-vertical");
        this._widget.setMarginTop(10);
        this._widget.setHeight(8);
        this._widget.resetWidth();
      } else {
        this._widget.setDecorator("separator-horizontal");
        this._widget.setMarginLeft(10);
        this._widget.resetHeight();
        this._widget.setWidth(8);
      }
    },

    /* Apply collected gui properties to this widet
     * */
    _applyGuiProperties: function(props){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(!props){
        return;
      }

      if(props["orientation"] && props["orientation"]["enum"]){
        this._setOrientation(props["orientation"]["enum"]);
      }
    }
  }
});

// vim:tabstop=2:expandtab:shiftwidth=2
