/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Dashboard widget with optional title and/or line. Can be used to optically separate widgets from each other.
 */
qx.Class.define("gosa.plugins.separator.Main", {
  extend : gosa.plugins.AbstractDashboardWidget,

  construct : function() {
    this.base(arguments);
    this.getChildControl("container").setLayout(new qx.ui.layout.HBox());
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-dashboard-widget-separator"
    },

    borderPosition: {
      check: ["top", "bottom", "none"],
      init: "none",
      apply: "_applyBorderPosition"
    }
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  members : {

    // property apply
    _applyBorderPosition: function(value, old) {
      if (old !== "none") {
        this.removeState("border"+old);
      }
      if (value !== "none") {
        this.addState("border"+value);
      }
    },

    draw: function() {
      this.getChildControl("title").setLayoutProperties({flex: 1});
    }
  },

  defer: function () {
    gosa.data.DashboardController.registerWidget(gosa.plugins.separator.Main, {
      displayName: qx.locale.Manager.tr("Separator"),
      icon: "@Ligature/minus",
      resizable: [false, true, false, true],
      theme: {
        appearance : gosa.plugins.separator.Appearance,
        decoration : gosa.plugins.separator.Decoration
      },
      defaultColspan: 6,
      requiresConfiguration: true,
      settings: {
        properties: {
          title: {
            type: "String",
            title: qx.locale.Manager.tr("Title")
          },
          font: {
            type: "selection",
            provider: "custom",
            defaultValue: "Title",
            options: [
              { data: "default", label: qx.locale.Manager.tr("Normal") },
              { data: "bold", label: qx.locale.Manager.tr("Bold") }
            ],
            title: qx.locale.Manager.tr("Font")
          },
          borderPosition: {
            type: "selection",
            provider: "custom",
            defaultValue: "none",
            options: [
              { data: "none", label: qx.locale.Manager.tr("No border")},
              { data: "top", label: qx.locale.Manager.tr("Top border")},
              { data: "bottom", label: qx.locale.Manager.tr("Bottom border")}
            ],
            title: qx.locale.Manager.tr("Border position")
          }
        }
      }
    });
  }
});
