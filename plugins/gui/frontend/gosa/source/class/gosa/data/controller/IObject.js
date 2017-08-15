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
 * Interface for Object-/Workflow controllers
 */
qx.Interface.define("gosa.data.controller.IObject", {

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    modified: {
      check: "Boolean"
    }
  },

  members : {

    closeWidgetAndObject : function() {
    },

    /**
     * @return {gosa.data.util.ExtensionFinder}
     */
    getExtensionFinder : function() {
    },

    /**
     * @return {gosa.data.controller.Extensions}
     */
    getExtensionController : function() {
    },

    /**
     * @param attributeName {String}
     * @return {qx.ui.core.Widget | null} Existing attribute for the attribute name
     */
    getWidgetByAttributeName : function(attributeName) {
    },

    /**
     * @param attributeName {String}
     * @return {gosa.ui.widgets.QLabelWidget | null}
     */
    getBuddyByAttributeName : function(attributeName) {
    },

    getActiveExtensions : function() {
    }
  }

});
