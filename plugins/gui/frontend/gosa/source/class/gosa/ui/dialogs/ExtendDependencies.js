/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Dialog to request the user if dependent extensions shall be extended in addition to the extension the user
 * originally selected.
 */
qx.Class.define("gosa.ui.dialogs.ExtendDependencies", {
  extend : gosa.ui.dialogs.RetractDependencies,

  members : {
    _getListMessage : function() {
      return this.trn(
        "To extend the object by the <b>%1</b> extension, the following additional extension is required: %2",
        "To extend the object by the <b>%1</b> extension, the following additional extensions are required: %2",
        this._numberOfNames, this._getTranslatedExtension(this._extension).join(', '), this._list
      );
    },

    _getQuestion : function() {
      return this.trn(
        "Do you want the missing extension to be added?",
        "Do you want the missing extensions to be added?",
        this._dependencies.length
      );
    }
  }
});
