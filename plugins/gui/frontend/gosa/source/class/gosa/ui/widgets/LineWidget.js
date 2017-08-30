/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

qx.Class.define("gosa.ui.widgets.LineWidget",
{
  extend : gosa.ui.widgets.Widget,

  properties: {

    orientation : {
      init : "Qt::Horizontal",
      check : ["Qt::Horizontal", "Qt::Vertical"],
      apply : "_setOrientation",
      nullable: true
    }
  },

  destruct: function(){
    this._disposeObjects("_widget");

    // Remove all listeners and then set our values to null.
    qx.event.Registration.removeAllListeners(this); 

    this.setBuddyOf(null);
    this.setGuiProperties(null);
    this.setValues(null);
    this.setValue(null);
    this.setBlockedBy(null);
  }, 

  construct : function()
  {
    this.base(arguments);

    // Call super class
    this.contents.setLayout(new qx.ui.layout.Canvas());
    this._widget = new qx.ui.core.Widget();
    this.contents.add(this._widget, {top:0, bottom:0, left:0, right: 0});

    this._setOrientation("Qt::Horizontal");
    this.removeState("gosaInput");
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

    /**
     * Apply collected gui properties to this widet
     */
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
