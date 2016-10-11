/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Base class for dialogs that perform an action on the object. All action dialogs should
 * extend this class.
 */
qx.Class.define("gosa.ui.dialogs.actions.Base", {

  extend: gosa.ui.dialogs.Dialog,

  /**
   * @param actionController {gosa.data.ActionController}
   * @param caption {String}
   * @param icon {String}
   */
  construct: function(actionController, caption, icon) {
    this.base(arguments, caption, icon);
    qx.core.Assert.assertInstance(actionController, gosa.data.ActionController);
    this._actionController = actionController;
  },

  members : {
    _actionController : null
  },

  destruct : function() {
    this._disposeObjects("_actionController");
  }
});
