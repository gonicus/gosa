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
* The plugins appearance definition
*/
qx.Theme.define("gosa.plugins.workflowstarter.Appearance", {
  
  appearances: {
    "gosa-dashboard-widget-workflowstarter": {
      include: "gosa-dashboard-widget",
      alias: "gosa-dashboard-widget",

      style: function(states) {
        return {
          padding: 0,
          backgroundColor: states.edit ? "transparent" : (states.hovered ? "rgba(0, 0, 0, 0.1)" : "transparent")
        }
      }
    },

    "gosa-dashboard-widget-workflowstarter/workflow-item": {
      include : "gosa-workflow-item",
      alias : "gosa-workflow-item"
    },

    "gosa-dashboard-widget-workflowstarter/workflow-item/content": {
      style: function() {
        return {
          marginLeft: 10,
          marginRight: 10
        }
      }
    }
  }
});