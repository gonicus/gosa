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

qx.Class.define("gosa.ui.container.SlideBar",
{
  extend : qx.ui.container.SlideBar,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */

  /**
   * @param orientation {String?"horizontal"} The slide bar orientation
   */
  construct : function(orientation)
  {
    this.base(arguments);
  },

  properties :
  {
    menu :
    {
      init : null,
      nullable : true,
      apply : "_applyMenu"
    },

    // overridden
    appearance :
    {
      refine : true,
      init : "edit-slidebar"
    }
  },

  members : {
    _applyMenu : function(menu)
    {
      if (menu) {
        this._showChildControl("button-menu");
      } else {
        this._excludeChildControl("button-menu");
      }

      this.getChildControl("button-menu").setMenu(menu);
    },

    // overridden
    _createChildControlImpl : function(id, hash)
    {
      var control = null;

      switch (id) {
        case "button-menu":
          control = new qx.ui.form.MenuButton();
          this._addAt(control, 3);
          break;
      }

      return control || this.base(arguments, id);
    }
  }
});
