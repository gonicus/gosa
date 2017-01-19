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
        color: "rgba(255, 255, 255, 0.2)"
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

    "gosa-droppable": {
      style : {
        width: 1,
        style: "dashed",
        color: "mediumgray-dark"
      }
    },

    "gosa-droppable-hovered": {
      include: "gosa-droppable",

      style : {
        style: "solid",
        backgroundColor: "mediumgray-dark"
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
        color : "transparent",
        backgroundColor : "transparent"
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
        backgroundColor : "sunflower-dark",
        color : "sunflower-dark"
      }
    },

    "button-warning-focused": {
      include : "button-warning",
      style: {
        backgroundColor : "sunflower-light",
        color : "sunflower-light"
      }
    },

    "button-warning-pressed": {
      include : "button-normal-focused",
      style: {
        backgroundColor : "sunflower-light",
        color : "sunflower-light"
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
        backgroundColor : "lightgray-dark",
        color : "lightgray-dark"
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

    "popup" : {
      style: {
        backgroundColor : "white",
        width :1,
        color : "mediumgray-dark",
        radius : [0, 0, 0, 4],
        shadowLength     : [0, 6],
        shadowBlurRadius : 12,
        shadowColor      : "rgba(0, 0, 0, 0.175)"
      }
    },

    "menu" : {
      style: {
        backgroundColor : "darkgray-dark",
        radius : 4,
        shadowLength     : [0, 6],
        shadowBlurRadius : 12,
        shadowColor      : "rgba(0, 0, 0, 0.175)"
      }
    },

    "menu-separator" : {
      style: {
        widthTop    : 1,
        colorTop    : "darkgray-light"
      }
    },

    "menu-default" : {
      include : "menu",
      style: {
        backgroundColor : "white"
      }
    },

    "menu-default-separator" : {
      include : "menu-separator",
      style: {
        colorTop    : "darkgray-dark"
      }
    },

    "window-captionbar-active" :
    {
      style : {
        backgroundColor : "white"
      }
    },

    "window" : {
      style : {
        radius : 4,
        backgroundColor : "white",
        shadowLength     : [0, 0],
        shadowBlurRadius : 5,
        shadowColor      : "rgba(0, 0, 0, 0.4)"
      }
    },

    "window-maximized" : {
      include : "window",
      style : {
        radius : 0,
        shadowColor      : undefined
      }
    },

    "window-captionbar-inactive" :
    {
      style : {
        backgroundColor : "lightgray-light"
      }
    },

    "window-inactive" : {
      include : "window",
      style : {
        radius : 4,
        backgroundColor : "lightgray-light",
        shadowBlurRadius : 2
      }
    },

    "window-warning-captionbar-active" :
    {
      style : {
        backgroundColor : "#ffdd87"
      }
    },

    "window-warning" : {
      style : {
        radius : 4,
        backgroundColor : "#ffdd87"
      }
    },

    "window-error-captionbar-active" :
    {
      style : {
        backgroundColor : "#f2838f"
      }
    },

    "window-error" : {
      style : {
        radius : 4,
        backgroundColor : "#f2838f"
      }
    },

    "checkbox" : {
      style : {
        width : 1,
        color : "mediumgray-dark",
        backgroundColor : "white"
      }
    },

    "checkbox-checked" : {
      style : {
        width : 1,
        color : "aqua-dark",
        backgroundColor : "aqua-dark"
      }
    },

    "checkbox-disabled" : {
      style : {
        width : 1,
        color : "mediumgray-light",
        backgroundColor : "white"
      }
    },

    "checkbox-disabled-checked" : {
      style : {
        width : 1,
        color : "mediumgray-dark",
        backgroundColor : "mediumgray-dark"
      }
    },

    "checkbox-hovered" : {
      include : "checkbox",
      style : {
        color : "aqua-light"
      }
    },

    "checkbox-hovered-checked" : {
      include : "checkbox",
      style : {
        color : "aqua-light",
        backgroundColor : "aqua-light"
      }
    },

    "checkbox-invalid" : {
      style : {
        width : 1,
        color : "grapefruit-dark",
        backgroundColor : "white"
      }
    },

    "checkbox-checked-invalid" : {
      style : {
        width : 1,
        color : "grapefruit-dark",
        backgroundColor : "grapefruit-dark"
      }
    },

    "checkbox-hovered-invalid" : {
      include : "checkbox",
      style : {
        color : "grapefruit-light"
      }
    },

    "checkbox-hovered-checked-invalid" : {
      include : "checkbox",
      style : {
        color : "grapefruit-light",
        backgroundColor : "grapefruit-light"
      }
    },

    "selectbox-field" : {
      style: {
        backgroundColor : "white",
        color : "mediumgray-dark",
        radius : 4,
        width : 1
      }
    },

    "selectbox-field-invalid" : {
      include : "selectbox-field",
      style: {
        color : "grapefruit-dark"
      }
    },

    "selectbox-field-disabled" : {
      include : "selectbox-field",
      style: {
        backgroundColor : "lightgray-dark",
        color : "lightgray-dark"
      }
    },

    "selectbox-field-focused" : {
      include : "selectbox-field",
      style: {
        color : "aqua-dark"
      }
    },

    "selectbox-field-focused-invalid" : {
      include : "selectbox-field-focused",
      style: {
        color : "grapefruit-dark"
      }
    },

    "listitem" :
    {
      style: {
        color : "mediumgray-light",
        width : [0, 0, 1, 0],
        backgroundColor : "transparent"
      }
    },

    "listitem-selected" :
    {
      style: {
        color : "aqua-light",
        width : [0, 0, 1, 0],
        backgroundColor : "aqua-light"
      }
    },

    "spinner-button" :
    {
      style: {
        color : "mediumgray-dark",
        width : [0, 0, 0, 1]
      }
    },

    "spinner-button-focused" :
    {
      style: {
        color : "aqua-light",
        width : [0, 0, 0, 1]
      }
    },

    "tooltip" : {
      style: {
        radius : 4,
        width : 1,
        shadowLength : [0, 6],
        shadowBlurRadius : 12,
        shadowColor : "rgba(0, 0, 0, 0.175)"
      }
    },

    "panel" :
    {
      style :
      {
        color : "lightgray-dark",
        width : 1,
        radius : 4
      }
    },

    "table" :
    {
      style :
      {
        backgroundColor : "white",
        color : "mediumgray-dark",
        width : 1,
        radius : [0, 0, 4, 4]
      }
    },

    "table-header" :
    {
      style :
      {
        widthBottom : 2,
        color : "lightgray-dark"
      }
    },

    "table-header-cell" :
    {
      style :
      {
        widthRight : 1,
        color : "lightgray-dark"
      }
    },

    "table-header-cell-first" :
    {
      include : "table-header-cell",
      style : {
        widthLeft : 1
      }
    },

    "bread-crumb" :
    {
      style : {
        width : 1,
        color : "lightgray-dark",
        radius : 4
      }
    },

    "bread-crumb-item-last" :
    {
      style : {
        backgroundColor : "transparent"
      }
    },

    "bread-crumb-item-arrow" :
    {
      style : {
        width : [18, 0, 18, 11],
        color : ["transparent", "rgba(0, 0, 0, 0.15)", "transparent", "rgba(0, 0, 0, 0.15)"]
      }
    },

    "bread-crumb-item-arrow-inner" :
    {
      style : {
        width : [18, 0, 18, 11],
        color : ["transparent", "aqua-dark", "transparent", "aqua-dark"]
      }
    },

    "bread-crumb-item-arrow-inner-pressed" :
    {
      include : "bread-crumb-item-arrow-inner",
      style : {
        color : ["transparent", "aqua-light", "transparent", "aqua-light"]
      }
    }

    // Do NOT place any decorations here, that are not FLAT theme related. Put them above
    // the marker above.
  }
});
