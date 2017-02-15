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

      switch(id)
      {
        case "button-menu":
          control = new qx.ui.form.MenuButton();
          this._addAt(control, 3);
          break;

        case "button-forward":
          control = new qx.ui.form.RepeatButton;
          control.addListener("execute", this._onExecuteForward, this);
          control.setFocusable(false);
          this._addAt(control, 2);
          break;

        case "button-backward":
          control = new qx.ui.form.RepeatButton;
          control.addListener("execute", this._onExecuteBackward, this);
          control.setFocusable(false);
          this._addAt(control, 0);
          break;

        case "content":
          control = new qx.ui.container.Composite();

          /*
           * Gecko < 2 does not update the scroll position after removing an
           * element. So we have to do this by hand.
           */
          if (qx.core.Environment.get("engine.name") == "gecko" &&
            parseInt(qx.core.Environment.get("engine.version")) < 2)
          {
            control.addListener("removeChildWidget", this._onRemoveChild, this);
          }

          this.getChildControl("scrollpane").add(control);
          break;

        case "scrollpane":
          control = new qx.ui.core.scroll.ScrollPane();
          control.addListener("update", this._onResize, this);
          control.addListener("scrollX", this._onScroll, this);
          control.addListener("scrollY", this._onScroll, this);
          break;
      }

      return control || this.base(arguments, id);
    }
  }
});
