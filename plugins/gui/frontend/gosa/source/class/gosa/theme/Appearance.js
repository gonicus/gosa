/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

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
          textColor : states.focused | states.checked ? "header-bar" : "icon-color"
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
          textColor : "red",
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
          textColor : "green",
          cursor    : "default"
        };
      }
    },

    "search-list-item/title" : {
      style : function() {
        return {
          textColor : "blue",
          cursor    : "pointer",
          font      : "SearchResultTitle"
        };
      }
    },

    "search-list-item/description" : {
      style : function() {
        return {
          textColor : "text"
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

        var backgroundColor = states.hovered ? 'light-background' : undefined;

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
          backgroundColor : "#303030",
          height: 48
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

    "title-bar/sandwich": {
      include: "button",
      alias : "button",

      style : function()
      {
        return {
          icon: "@Ligature/menu",
          decorator: null,
          show : "icon",
          center: true
        };
      }
    },
    "title-bar/sandwich/icon": {
      include: "image",
      alias : "image",
      style: function() {
        return {
          width: 35,
          scale: true
        }
      }
    },
    "title-bar/search": {
      include: "textfield",
      alias: "textfield",

      style : function()
      {
        return {
          margin: 10,
          textColor: "font",
          minWidth: 300
        };
      }
    },

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
          textColor: states.selected | states.focused ? '#FFFFFF' : 'icon-color'
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
          textColor: states.selected | states.focused ? '#FFFFFF' : 'icon-color'
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
    "tree-view": "tabview-page",
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

      style: function() {
        return {
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
          width: 35,
          height: 35,
          scale: true
        }
      }
    },

    "gosa-spinner": {
      style: function() {
        return {
          textColor: "icon-color",
          opacity: 0.5,
          show: "icon",
          size: 30,
          center: true
        };
      }
    }
  }
});
