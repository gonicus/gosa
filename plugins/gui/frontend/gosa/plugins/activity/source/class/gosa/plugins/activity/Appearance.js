/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* The activities plugin appearance definition
*/
qx.Theme.define("gosa.plugins.activity.Appearance", {

  appearances: {
    "gosa-dashboard-widget-activities": "gosa-dashboard-widget",
    "gosa-dashboard-widget-activities/list": {
      include: "list",
      alias: "list",

      style: function() {
        return {
          backgroundColor: "transparent",
          decorator: null
        }
      }
    },

    "gosa-plugins-actitivies-item": {
      include: "search-list-item",
      alias: "search-list-item",
      style: function() {
        return {
          overlayIconSize: 20
        }
      }
    },
    "gosa-plugins-actitivies-item/icon": {
      style: function() {
        return {
          width: 30,
          height: 30,
          marginRight: 10,
          alignY: "middle",
          alignX: "center",
          scale: true
        }
      }
    }
  }
});