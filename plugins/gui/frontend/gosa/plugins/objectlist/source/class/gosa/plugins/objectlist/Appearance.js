/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
*
*/
qx.Theme.define("gosa.plugins.objectlist.Appearance", {

  appearances: {
    "gosa-dashboard-widget-objectlist": "gosa-dashboard-widget",
    "gosa-dashboard-widget-objectlist/list": {
      include: "list",
      alias: "list",

      style: function() {
        return {
          backgroundColor: "transparent",
          decorator: null
        }
      }
    },

    "gosa-plugins-objectlist-item": {
      include: "search-list-item",
      alias: "search-list-item",
      style: function() {
        return {
          overlayIconSize: 20
        }
      }
    },
    "gosa-plugins-objectlist-item/icon": {
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