/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Theme.define("gosa.plugins.separator.Decoration", {
  decorations : {
    "gosa-dashboard-widget-separator-top": {
      style: {
        width: [1, 0, 0, 0],
        color: "black"
      }
    },
    "gosa-dashboard-widget-separator-bottom": {
      style: {
        width: [0, 0, 1, 0],
        color: "black"
      }
    }
  }
});
