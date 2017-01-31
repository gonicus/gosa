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
qx.Class.define("gosa.plugins.###NAME_LOWER###.Main", {
  extend : gosa.plugins.AbstractDashboardWidget,

  construct : function() {
    this.base(arguments);
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-dashboard-widget-###NAME_LOWER###"
    }
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  members : {

    draw: function() {
      // add your code here
    }
  },

  defer: function () {
    gosa.data.controller.Dashboard.registerWidget(gosa.plugins.###NAME_LOWER###.Main, {
      displayName: qx.locale.Manager.tr("###NAME###"),
      defaultColspan: 3,
      defaultRowspan: 1,
      theme: {
        appearance : gosa.plugins.###NAME_LOWER###.Appearance
      }
    });
  }
});