/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Theme.define("gosa.plugins.separator.Appearance", {
  
  appearances: {
    "gosa-dashboard-widget-separator": {
      style: function(states) {
        var dc = null;
        if (states.bordertop) {
          dc = "gosa-dashboard-widget-separator-top";
        } else if (states.borderbottom) {
          dc = "gosa-dashboard-widget-separator-bottom";
        }
        return {
          decorator: dc
        }
      }
    },
    "gosa-dashboard-widget-separator/title": {
      style: function() {
        return {
          alignY: "middle"
        }
      }
    }
  }
});
