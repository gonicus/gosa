/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Theme.define("gosa.theme.Decoration",
{
  extend : qx.theme.indigo.Decoration,

  decorations :
  {
    "background" :
    {
      style :
      {
        backgroundImage  : "gosa/images/background.png",
        backgroundRepeat : "repeat"
      }
    },

    "title-bar" : {},

    "gosa-workflow-item": {
      style: {
        width: 1,
        radius: 10,
        color: "icon-color",
        startColorPosition: 0,
        endColorPosition: 100,
        startColor: "#FFFFFF",
        endColor: "#DDDDDD"
      }
    },

    "gosa-listitem-window": {
      style: {
        width: [0, 1, 0, 1],
        color: ["#606060", "#606060", "#A0A0A0", "#A0A0A0"]
      }
    },
    "gosa-workflow-category": {
      style: {
        width: [1, 0 , 0, 0],
        color: "font"
      }
    },
    "gosa-dashboard-widget": {
      style: {
        width: 1,
        color: "#EEE"
      }
    },
    "gosa-dashboard-widget-edit": {
      style: {
        width: 2,
        color: "#000"
      }
    }
  }
});
