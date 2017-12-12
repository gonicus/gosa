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

/**
 * Interface objects that can dynamically create {@link gosa.ui.dialogs.TemplateDialog} objects.
 */
qx.Interface.define("gosa.data.controller.ITemplateDialogCreator", {

  members : {

    /**
     * @return {Objects} Model data (attribute name => value)
     */
    getObjectData : function() {
    },

    /**
     * @return {qx.ui.window.Window} Adds a dialog that shall be managed
     */
    addDialog : function(dialog) {
    }
  }
});
