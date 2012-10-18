/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.widgets.QPushButtonWidget",
{
  extend : gosa.ui.widgets.Widget,

  properties: {

    // The buttons text
    text : {
      init : "",
      check : "String",
      apply : "_setText",
      nullable: true
    }
  },

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
      this._widget.setLabel(this['tr'](value));
    },

    /* Apply collected gui properties to this widet
     * */
    _applyGuiProperties: function(props){

      // This happens when this widgets gets destroyed - all properties will be set to null.
      if(!props){
        return;
      }

      if(props["text"] && props["text"]["string"]){
        this._setText(props["text"]["string"]);
      }
    }
  }
});

// vim:tabstop=2:expandtab:shiftwidth=2
