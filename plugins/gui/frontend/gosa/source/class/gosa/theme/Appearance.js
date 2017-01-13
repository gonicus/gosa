/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Theme.define("gosa.theme.Appearance",
{
  extend : qx.theme.indigo.Appearance,

  appearances : {
    "mergeButton" : {
      style : function(states) {
        var style = {};
        style['backgroundColor'] = null;
        style['icon'] = null;
        style['padding'] = 4;
        style['paddingLeft'] = 22;
        if (states['checked']) {
          style['paddingLeft'] = 0;
          style['backgroundColor'] = '#EDEDED';
          style['icon'] = 'gosa/images/22/actions/dialog-ok-apply.png';
        }
        return (style);
      }
    },

    "tabview" : {
      style : function()
      {
        return {
          contentPadding: 0
        };
      }
    },

    "tabview-page/button/label" : {
      alias : "label",

      style : function(states) {
        return {
          font : states.focused ? 'underline' : 'default'
        };
      }
    },

    "tabview-page/button/icon" : {

      style : function(states) {
        return {
          textColor : states.focused || states.checked ? "header-bar" : "icon-color"
        };
      }
    },

    "table" : {
      style : function(states) {
        if (states.invalid) {
          return ({decorator : "border-invalid"});
        }
        else {
          return ({decorator : null});
        }
      }
    },

    "SearchAid" : {},

    "SearchAid/legend" : {
      alias : "atom",

      style : function() {
        return {
          textColor : "#808080",
          padding   : [5, 0, 0, 5],
          font      : "bold"
        };
      }
    },

    "SearchAid/frame" : {
      style : function() {
        return {
          backgroundColor : "background",
          padding         : [5, 0, 0, 5],
          margin          : [10, 0, 0, 0],
          decorator       : null
        };
      }
    },

    "SearchAidButton-frame" : {
      alias : "atom",

      style : function(states) {
        var weight;
        if (states.pressed || states.abandoned || states.checked) {
          weight = "bold";
        }
        else {
          weight = "default";
        }

        return {
          textColor : "bittersweet-dark",
          font      : weight
        };
      }
    },

    "SearchAidButton" : {
      alias   : "SearchAidButton-frame",
      include : "SearchAidButton-frame",

      style : function(states) {
        return {
          center : false,
          cursor : states.disabled ? undefined : "pointer"
        };
      }
    },

    "attribute-button-frame" : {
      alias : "atom",

      style : function(states)
      {
        var decorator;

        if (!states.disabled) {
          if (states.hovered && !states.pressed && !states.checked) {
            decorator = "button-box-hovered";
          }
          else if (states.hovered && (states.pressed || states.checked)) {
            decorator = "button-box-pressed-hovered";
          }
          else if (states.pressed || states.checked) {
            decorator = "button-box-pressed";
          }
        }

        return {
          decorator : decorator,
          padding   : [3, 7],
          cursor    : states.disabled ? undefined : "pointer",
          minWidth  : 28,
          minHeight : 28
        };
      }
    },

    "attribute-button" : {
      alias   : "attribute-button-frame",
      include : "attribute-button-frame",

      style : function() {
        return {
          center : true
        };
      }
    },

    "SearchList" : {
      alias : "scrollarea"
      //,include : "textfield"
    },

    "search-list-item/icon" : {
      style : function() {
        return {
          width       : 64,
          scale       : true,
          marginRight : 5,
          textColor   : "icon-color"
        };
      }
    },

    "search-list-item/dn" : {
      style : function() {
        return {
          textColor : "#006442",
          cursor    : "default"
        };
      }
    },

    "search-list-item/title" : {
      style : function() {
        return {
          textColor : "#1F4788",
          cursor    : "pointer",
          font      : "SearchResultTitle"
        };
      }
    },

    "search-list-item/description" : {
      style : function() {
        return {
          textColor : "darkgray-dark"
        };
      }
    },

    "search-list-item" : {
      alias : "atom",

      style : function(states) {
        var padding = [3, 5, 3, 5];
        if (states.lead) {
          padding = [2, 4, 2, 4];
        }
        if (states.dragover) {
          padding[2] -= 2;
        }

        var backgroundColor = states.hovered ? 'lightgray-light' : undefined;

        return {
          padding         : padding,
          marginBottom    : 10,
          backgroundColor : backgroundColor,
          decorator       : states.lead ? "lead-item" : states.dragover ? "dragover" : undefined
        };
      }
    },

    "search-list-item/throbber-pane": {
      style: function() {
        return {
          backgroundColor: '#000000',
          opacity: 0.2
        }
      }
    },

    "title-bar": {
      style: function()  {
        return {
          textColor: "header-text",
          //backgroundColor : "darkgray-dark",
          backgroundColor : "bittersweet-dark",
          height: 40
        }
      }
    },

    "title-bar/logo": {
      style: function() {
        return {
          gap : 3,
          paddingLeft: 5,
          paddingRight: 10,
          font : "Logo"
        }
      }
    },

    "title-bar/logo/icon": {
      style: function() {
        return {
          paddingTop: 3
        }
      }
    },

    "title-bar/windows": {
      style: function() {
        return {
          backgroundColor: "transparent"
        }
      }
    },

    "title-bar/user": {
      include: "button-normal",
      alias : "button-normal",

      style : function(states)
      {
        return {
          gap : 10,
          decorator: null,
          center: true,
          backgroundColor : states.hovered ? "bittersweet-light" : "transparent"
        };
      }
    },

    "title-bar/user/icon": {
      include: "image",
      alias : "image",
      style: function() {
        return {
          width: 32,
          height: 32,
          scale: true
        }
      }
    },

    "gosa-tabview-page-dashboard" : "gosa-tabview-page",
    "gosa-tabview-page-dashboard/edit-mode": {
      include: "button",
      alias: "button",

      style: function(states) {
        return {
          decorator: states.hovered ? "gosa-dashboard-edit-hover" : null,
          icon : "@Ligature/gear",
          allowGrowX: false,
          alignX: "right",
          padding: [3, 3, 10, 10]
        }
      }
    },
    "gosa-tabview-page-dashboard/edit-mode/icon": {
      include: "image",
      alias : "image",
      style: function() {
        return {
          width: 22,
          scale: true
        }
      }
    },
    "gosa-tabview-page-dashboard/board": {
      style: function() {
        return {
          padding: [0, 16]
        }
      }
    },

    "gosa-tabview-page-workflows": "gosa-tabview-page",
    "gosa-tabview-page-workflows/list": "gosa-tabview-page-dashboard/board",

    "statusLabel": {
      include: "label",

      style : function(states) {

        var tc = null;
        if (states.error) {
          tc = "error-text";
        }

        return {
          textColor: tc
        };
      }
    },
    "icon-menu-button": "menu-button",
    "icon-menu-button/icon": {
      include: "menu-button/icon",
      alias: "menu-button/icon",

      style: function(states) {

        return  {
          width: 22,
          height: 22,
          scale: true,
          textColor: states.selected || states.focused ? '#FFFFFF' : 'icon-color'
        }
      }
    },

    "virtual-tree-folder/icon": {
      include: "image",
      alias: "image",

      style: function(states) {
        return {
          width: 22,
          height: 22,
          scale: true,
          textColor: states.selected || states.focused ? '#FFFFFF' : 'icon-color'
        }
      }
    },

    "slidebar/button-menu": {
      include: "menubutton",
      alias: "menubutton",

      style: function() {
        return {
          icon   : "@Ligature/gear",
          margin : 4
        }
      }
    },
    "slidebar/button-menu/icon": {
      include: "image",

      style: function() {
        return {
          width: 22,
          scale: true
        }
      }
    },
    "tree-view": "gosa-tabview-page",
    "tree-view/search-field": {
      include: "textfield",
      alias: "textfield",

      style: function() {
        return {
          marginTop: 8,
          width: 200
        }
      }
    },
    "tree-view/splitpane": "splitpane",
    "tree-view/table": "table",
    "tree-view/delete-button": "icon-menu-button",
    "tree-view/open-button": "icon-menu-button",
    "tree-view/action-menu-button": "toolbar-menubutton",
    "tree-view/filter-menu-button": "toolbar-menubutton",
    "tree-view/create-menu-button": "toolbar-menubutton",

    "gosa-workflow-item": {

      style: function(states) {
        return {
          show: "both",
          icon: "@Ligature/app",
          iconSize: 40,
          allowGrowX: false,
          backgroundColor: states.hovered ? "hovered" : "transparent",
          cursor: states.hovered ? "pointer" : "default",
          margin: 5,
          padding: 10
        }
      }
    },
    "gosa-workflow-item/content": {
      style: function() {
        return {
          marginLeft: 10,
          width: 250
        }
      }
    },
    "gosa-workflow-category": {
      include: "atom",
      alias: "atom",

      style: function(states) {
        return {
          show: "label",
          font: "Title",
          textColor: "font",
          decorator: states.first ? null : "gosa-workflow-category",
          marginTop: 10
        }
      }
    },
    "gosa-workflow-item/throbber": {
      include: "gosa-throbber",

      style: function() {
        return {
          textColor: "icon-color"
        };
      }
    },
    "gosa-workflow-item/label": {
      style: function() {
        return {
          font : "Subtitle"
        };
      }
    },

    "gosa-tabview-page": "tabview-page",
    "gosa-tabview-page/button/icon": {
      include: "tabview-page/button/icon",
      style: function() {
        return {
          width: 35,
          scale: true
        }
      }
    },
    "edit-tabview-page" : "tabview-page",
    "edit-tabview-page/button/icon": {
      include: "tabview-page/button/icon",
      style: function() {
        return {
          width: 22,
          height: 22,
          scale: true
        }
      }
    },

    "gosa-listitem-window": {
      include: "listitem",
      alias: "listitem",

      style: function(states) {
        return {
          backgroundColor : states.selected ? "bittersweet-light" : undefined,
          decorator: "gosa-listitem-window",
          width: 180,
          gap: 8,
          center: true,
          allowGrowX: false,
          allowShrinkX: false
        }
      }
    },
    "gosa-listitem-window/icon": {
      include: "listitem/icon",

      style: function() {
        return {
          width: 32,
          height: 32,
          scale: true
        }
      }
    },

    "gosa-spinner": {
      style: function(states) {
        return {
          textColor: "icon-color",
          backgroundColor: states.blocking ? "rgba(0,0,0,0.1)" : "transparent",
          opacity : 0.5,
          show: "icon",
          size: 30,
          zIndex: 10000,
          center: true
        };
      }
    },

    "gosa-dashboard-widget": {
      style: function(states) {
        var op = 1.0;
        var dc = "gosa-dashboard-widget";
        if (states.selected) {
          dc += "-selected";
        } else if (states.edit) {
          dc += "-edit";
          op = 0.5;
        }
        return {
          padding: 10,
          opacity: op,
          decorator: dc
        }
      }
    },
    "gosa-dashboard-widget/title": {
      style: function() {
        return {
          font: "Subtitle"
        }
      }
    },
    "gosa-dashboard-edit-button": {
      style: function() {
        return {
          iconPosition: "top",
          margin: 10,
          padding: 10,
          width: 100
        }
      }
    },

    // - FLAT - do not insert anything behind this marker -----------------------------------------------------

    "button" : {
      style: function(states) {
        var styles = {
          decorator : "button-default",
          textColor : "darkgray-dark",
          padding : [6, 12],
          opacity : undefined,
          font : "default"
        };

        if (states.disabled) {
          styles.opacity = 0.45;
        }
        else if (states.hovered || states.focused || states.pressed) {
          styles.decorator = states.pressed ? "button-default-pressed" : "button-default-focused";
        }

        return styles;
      }
    },

    "button-normal" : {
      include : "button",
      style: function(states) {
        var styles = {
          decorator : "button-normal",
          textColor : "white"
        };

        if (!states.disabled && (states.hovered || states.focused || states.pressed)) {
          styles.decorator = states.pressed ? "button-normal-pressed" : "button-normal-focused";
        }

        return styles;
      }
    },

    "button-link" : {
      include : "button",
      style: function(states) {
        var styles = {
          decorator : "button-link"
        };
        if (!states.disabled && (states.hovered || states.focused || states.pressed)) {
          styles.decorator = states.pressed ? "button-normal-pressed" : "button-normal-focused";
        }
        return styles;
      }
    },

    "button-default" : "button",

    "button-primary" : {
      include : "button",
      style: function(states) {
        var styles = {
          textColor : "white",
          decorator : "button-primary"
        };
        if (!states.disabled && (states.hovered || states.focused || states.pressed)) {
          styles.decorator = states.pressed ? "button-primary-pressed" : "button-primary-focused";
        }
        return styles;
      }
    },

    "button-success" : {
      include : "button",
      style: function(states) {
        var styles = {
          textColor : "white",
          decorator : "button-success"
        };
        if (!states.disabled && (states.hovered || states.focused || states.pressed)) {
          styles.decorator = states.pressed ? "button-success-pressed" : "button-success-focused";
        }
        return styles;
      }
    },

    "button-info" : {
      include : "button",
      style: function(states) {
        var styles = {
          textColor : "white",
          decorator : "button-info"
        };
        if (!states.disabled && (states.hovered || states.focused || states.pressed)) {
          styles.decorator = states.pressed ? "button-info-pressed" : "button-info-focused";
        }
        return styles;
      }
    },

    "button-warning" : {
      include : "button",
      style: function(states) {
        var styles = {
          textColor : "white",
          decorator : "button-warning"
        };
        if (!states.disabled && (states.hovered || states.focused || states.pressed)) {
          styles.decorator = states.pressed ? "button-warning-pressed" : "button-warning-focused";
        }
        return styles;
      }
    },

    "button-danger" : {
      include : "button",
      style: function(states) {
        var styles = {
          textColor : "white",
          decorator : "button-danger"
        };
        if (!states.disabled && (states.hovered || states.focused || states.pressed)) {
          styles.decorator = states.pressed ? "button-danger-pressed" : "button-danger-focused";
        }
        return styles;
      }
    },

    "textfield" :
    {
      style : function(states)
      {
        var decorator;

        var focused = !!states.focused;
        var invalid = !!states.invalid;
        var disabled = !!states.disabled;

        if (focused && invalid && !disabled) {
          decorator = "textfield-invalid";
        } else if (focused && !invalid && !disabled) {
          decorator = "textfield-focused";
        } else if (disabled) {
          decorator = "textfield-disabled";
        } else if (!focused && invalid && !disabled) {
          decorator = "textfield-invalid";
        } else {
          decorator = "textfield-normal";
        }

        var textColor;
        if (states.disabled) {
          decorator = "textfield-disabled";
          textColor = "darkgray-dark";
        } else if (states.showingPlaceholder) {
          textColor = "lightgray-dark";
        } else {
          textColor = "darkgray-dark";
        }

        return {
          decorator : decorator,
          padding : [ 6, 12 ],
          textColor : textColor
        };
      }
    },

    "menu" :
    {
      style : function(states)
      {
        var result =
        {
          decorator : "menu",
          spacingX : 6,
          spacingY : 0,
          padding : [4, 0, 4, 0],
          iconColumnWidth : 16,
          arrowColumnWidth : 4,
          placementModeY : states.submenu || states.contextmenu ? "best-fit" : "keep-align"
        };

        if (states.submenu)
        {
          result.position = "right-top";
          result.offset = [-2, -3];
        }

        return result;
      }
    },

    "menu-separator" :
    {
      style : function(states)
      {
        return {
          height : 0,
          decorator : "menu-separator",
          margin    : [ 4, 2 ]
        };
      }
    },

    "menu-button" :
    {
      alias : "atom",

      style : function(states)
      {
        return {
          textColor : states.disabled ? "darkgray-light" : "white",
          backgroundColor : states.selected ? "darkgray-light" : undefined,
          padding   : [ 5, 20 ]
        };
      }
    }
  }
});
