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
qx.Theme.define("gosa.plugins.yql.Appearance", {

  appearances: {
    "gosa-dashboard-widget-yql": "gosa-dashboard-widget",
    "gosa-dashboard-widget-yql/list": {
      include : "list",
      alias   : "list",

      style : function() {
        return {
          backgroundColor : "transparent",
          decorator       : null
        }
      }
    },

    "yql-listitem": {
      style: function(states) {
        return {
          decorator: "listitem",
          backgroundColor: states.hovered ? "hovered" : "transparent",
          padding: [5, 0]
        }
      }
    },

    "yql-listitem/label": {
      style: function() {
        return {
          font: "bold"
        }
      }
    },

    "yql-listitem/icon": {
      style: function() {
        return {
          width: 30,
          height: 30,
          scale: true,
          marginRight: 10,
          alignY: "middle",
          alignX: "center"
        }
      }
    },

    "yql-listitem/description": {
      style: function() {
        return {
          font: "small"
        }
      }
    }
  }
});