/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

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
    },
    "gosa-dashboard-widget-selected": {
      style: {
        width: 2,
        color: "#00405e"
      }
    },
    "gosa-dashboard-edit-hover": {
      style: {
        radiusBottomLeft: 22,
        backgroundColor: "#DDD"
      }
    },

    // - FLAT - do not insert anything behind this marker -----------------------------------------------------

    "button-normal": {
      style: {
        radius : 4,
        backgroundColor : "mediumgray-dark",
        color : "mediumgray-dark",
        width : 1
      }
    },

    "button-normal-focused": {
      include : "button-normal",
      style: {
        backgroundColor : "mediumgray-light",
        color : "mediumgray-light"
      }
    },

    "button-normal-pressed": {
      include : "button-normal-focused",
      style: {
        backgroundColor  : "mediumgray-light",
        color            : "mediumgray-light",
        inset            : true,
        shadowLength     : [0, 1],
        shadowBlurRadius : 2,
        shadowColor      : "rgba(0, 0, 0, 0.125)"
      }
    },

    "button-link": {
      include : "button-normal",
      style: {
        backgroundColor : undefined
      }
    },

    "button-default": {
      include : "button-normal",
      style: {
        backgroundColor : "white"
      }
    },

    "button-default-focused": {
      include : "button-normal-focused"
    },

    "button-default-pressed": {
      include : "button-normal-pressed"
    },

    "button-primary": {
      include : "button-normal",
      style: {
        backgroundColor : "aqua-dark",
        color : "aqua-dark"
      }
    },

    "button-primary-focused": {
      include : "button-primary",
      style: {
        backgroundColor : "aqua-light",
        color : "aqua-light"
      }
    },

    "button-primary-pressed": {
      include : "button-normal-focused",
      style: {
        backgroundColor : "aqua-light",
        color : "aqua-light"
      }
    },

    "button-success": {
      include : "button-normal",
      style: {
        backgroundColor : "grass-dark",
        color : "grass-dark"
      }
    },

    "button-success-focused": {
      include : "button-success",
      style: {
        backgroundColor : "grass-light",
        color : "grass-light"
      }
    },

    "button-success-pressed": {
      include : "button-normal-focused",
      style: {
        backgroundColor : "grass-light",
        color : "grass-light"
      }
    },

    "button-info": {
      include : "button-normal",
      style: {
        backgroundColor : "mint-dark",
        color : "mint-dark"
      }
    },

    "button-info-focused": {
      include : "button-info",
      style: {
        backgroundColor : "mint-light",
        color : "mint-light"
      }
    },

    "button-info-pressed": {
      include : "button-normal-focused",
      style: {
        backgroundColor : "mint-light",
        color : "mint-light"
      }
    },

    "button-warning": {
      include : "button-normal",
      style: {
        backgroundColor : "mint-dark",
        color : "mint-dark"
      }
    },

    "button-warning-focused": {
      include : "button-warning",
      style: {
        backgroundColor : "mint-light",
        color : "mint-light"
      }
    },

    "button-warning-pressed": {
      include : "button-normal-focused",
      style: {
        backgroundColor : "mint-light",
        color : "mint-light"
      }
    },

    "button-danger": {
      include : "button-normal",
      style: {
        backgroundColor : "grapefruit-dark",
        color : "grapefruit-dark"
      }
    },

    "button-danger-focused": {
      include : "button-warning",
      style: {
        backgroundColor : "grapefruit-light",
        color : "grapefruit-light"
      }
    },

    "button-danger-pressed": {
      include : "button-normal-focused",
      style: {
        backgroundColor : "grapefruit-light",
        color : "grapefruit-light"
      }
    },

    "textfield-normal" : {
      style: {
        backgroundColor : "white",
        color : "mediumgray-dark",
        radius : 4,
        width : 1
      }
    },

    "textfield-disabled" : {
      include : "textfield-normal",
      style: {
        backgroundColor : "lightgray-dark"
      }
    },

    "textfield-invalid" : {
      include : "textfield-normal",
      style: {
        color : "grapefruit-dark"
      }
    },

    "textfield-focused" : {
      include : "textfield-normal",
      style: {
        color : "aqua-dark"
      }
    },

    "menu" : {
      style: {
        backgroundColor : "darkgray-dark",
        radius : 4
      }
    },

    "menu-separator" : {
      style: {
        widthTop    : 1,
        colorTop    : "darkgray-light"
      }
    }
  }
});
