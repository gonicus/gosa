/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

qx.Theme.define("gosa.theme.Appearance", {
  extend: qx.theme.indigo.Appearance,

  appearances: {
    "window/progress": "progressbar",
    "merge-button": {
      style: function(states) {
        return {
          backgroundColor: states.checked ? 'lightgray-dark' : 'white',
          icon: states.checked ? "@Ligature/check/22" : "@Ligature/ban/22",
          padding: 10,
          maxWidth: 300
        };
      }
    },

    "merge-button/icon": {
      style: function(states) {
        return {
          textColor: states.checked ? "grass-dark" : "mediumgray-light"
        };
      }
    },

    "tabview": {
      style: function() {
        return {
          contentPadding: 0
        };
      }
    },

    "tabview-page/button/label": {
      alias: "label",

      style: function() {
        return {
          textColor: "darkgray-dark"
        };
      }
    },

    "tabview-page/button/icon": {

      style: function(states) {
        return {
          textColor: states.focused || states.checked ? "header-bar" : "icon-color"
        };
      }
    },

    "table": {
      style: function(states) {
        if (states.invalid) {
          return ({decorator: "border-invalid"});
        }
        else {
          return ({decorator: null});
        }
      }
    },

    "SearchAid": {},

    "SearchAid/legend": {
      alias: "atom",

      style: function() {
        return {
          textColor: "#808080",
          padding: [5, 0, 0, 5],
          font: "bold"
        };
      }
    },

    "SearchAid/frame": {
      style: function() {
        return {
          backgroundColor: "background",
          padding: [5, 0, 0, 5],
          margin: [10, 0, 0, 0],
          decorator: null
        };
      }
    },

    "SearchAidButton-frame": {
      alias: "atom",

      style: function(states) {
        var weight;
        if (states.pressed || states.abandoned || states.checked) {
          weight = "bold";
        }
        else {
          weight = "default";
        }

        return {
          textColor: "bittersweet-dark",
          font: weight
        };
      }
    },

    "SearchAidButton": {
      alias: "SearchAidButton-frame",
      include: "SearchAidButton-frame",

      style: function(states) {
        return {
          center: false,
          cursor: states.disabled ? undefined : "pointer"
        };
      }
    },

    "attribute-button-frame": {
      alias: "atom",

      style: function(states) {
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
          decorator: decorator,
          padding: [3, 7],
          cursor: states.disabled ? undefined : "pointer",
          minWidth: 28,
          minHeight: 28
        };
      }
    },

    "attribute-button": {
      alias: "attribute-button-frame",
      include: "attribute-button-frame",

      style: function() {
        return {
          center: true
        };
      }
    },

    "SearchList": {
      alias: "scrollarea"
      //,include : "textfield"
    },

    "search-list-item/icon": {
      style: function() {
        return {
          width: 64,
          scale: true,
          marginRight: 5,
          textColor: "icon-color"
        };
      }
    },

    "search-list-item/overlay-icon": {
      style: function() {
        return {
          width: 32,
          scale: true,
          backgroundColor: "rgba(255,255,255,0.8)"
        };
      }
    },

    "search-list-item/dn": {
      style: function() {
        return {
          textColor: "#006442",
          cursor: "default"
        };
      }
    },

    "search-list-item/toolbar": {
      style: function(states) {
        return {
          opacity : states.disabled ? 0 : 1
        };
      }
    },

    "search-list-item/title": {
      style: function(states) {
        return {
          textColor: "#1F4788",
          cursor: states.disabled ? undefined : "pointer",
          font: "SearchResultTitle"
        };
      }
    },

    "search-list-item/description": {
      style: function() {
        return {
          textColor: "darkgray-dark"
        };
      }
    },

    "search-list-item": {
      alias: "atom",

      style: function(states) {
        var padding = [3, 5, 3, 5];
        if (states.lead) {
          padding = [2, 4, 2, 4];
        }
        if (states.dragover) {
          padding[2] -= 2;
        }

        var backgroundColor = states.hovered && !states.disabled ? 'lightgray-light' : undefined;

        return {
          padding: padding,
          opacity: states.disabled ? 0.5 : 1,
          marginBottom: 10,
          backgroundColor: backgroundColor,
          decorator: states.lead ? "lead-item" : states.dragover ? "dragover" : undefined
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
      style: function() {
        return {
          textColor: "header-text", //backgroundColor : "darkgray-dark",
          backgroundColor: "bittersweet-dark",
          height: 40
        }
      }
    },

    "title-bar/logo": {
      style: function() {
        return {
          gap: 3,
          paddingLeft: 5,
          paddingRight: 10,
          font: "Logo"
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
      alias: "button-normal",

      style: function(states) {
        return {
          gap: 10,
          decorator: null,
          center: true,
          backgroundColor: states.hovered ? "bittersweet-light" : "transparent"
        };
      }
    },

    "title-bar/user/icon": {
      include: "image",
      alias: "image",
      style: function() {
        return {
          width: 32,
          height: 32,
          scale: true
        }
      }
    },

    "gosa-tabview-page-dashboard": {
      include: "gosa-tabview-page",
      alias: "gosa-tabview-page",

      style: function() {
        return {
          paddingTop: 8
        }
      }
    },

    "gosa-tabview-page-dashboard/toolbar": {
      style: function() {
        return {
          decorator : "panel",
          backgroundColor: "lightgray-dark"
        }
      }
    },

    "gosa-tabview-page-dashboard/edit-mode": {
      include: "button",
      alias: "button",

      style: function(states) {
        return {
          decorator: states.hovered ? "gosa-dashboard-edit-hover" : undefined,
          icon: "@Ligature/gear",
          padding: [0, 0, 5, 5]
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

    "gosa-tabview-page-dashboard/upload-dropbox": {
      style: function() {
        return {
          backgroundColor: "rgba(255,255,255,0.8)",
          zIndex: 100000
        }
      }
    },

    "gosa-tabview-page-workflows": "gosa-tabview-page",
    "gosa-tabview-page-workflows/toolbar": "gosa-tabview-page-dashboard/toolbar",
    "gosa-tabview-page-workflows/list": "gosa-tabview-page-dashboard/board",
    "gosa-tabview-page-workflows/edit-mode": "gosa-tabview-page-dashboard/edit-mode",

    "statusLabel": {
      include: "label",

      style: function(states) {

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

      style: function() {

        return {
          width: 22,
          height: 22,
          scale: true,
          textColor: 'white'
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
      include: "button-link",
      alias: "button-link",

      style: function() {
        return {
          icon: "@Ligature/gear",
          margin: 4
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
    "tree-view/bread-crumb": "bread-crumb",
    "tree-view/search-field": {
      include: "textfield",
      alias: "textfield",
      style: function() {
        return {
          margin: [8, 0]
        };
      }
    },

    "tree-view/splitpane": "splitpane",
    "tree-view/tree": "virtual-tree",
    "tree-view/delete-button": "icon-menu-button",
    "tree-view/open-button": "icon-menu-button",
    "tree-view/move-button": "icon-menu-button",
    "tree-view/action-menu-button": "toolbar-menubutton",
    "tree-view/filter-menu-button": "toolbar-menubutton",
    "tree-view/create-menu-button": "toolbar-menubutton",

    "tree-view/listcontainer": {
      style: function() {
        return {
          decorator: "panel"
        };
      }
    },

    "tree-view/table": {
      include: "table",
      alias: "table",
      style: function() {
        return {
          decorator: "table",
          margin: 6
        };
      }
    },

    "tree-view/toolbar": {
      style: function() {
        return {
          padding: [0, 20]
        }
      }
    },

    "gosa-workflow-item": {

      style: function(states) {
        var dc = null;
        if (states.selected) {
          dc = "gosa-workflow-item-selected";
        }
        else if (states.hovered) {
          dc = "gosa-workflow-item-hovered";
        }
        return {
          show: "both",
          icon: "@Ligature/app",
          iconSize: 64,
          allowGrowX: false,
          cursor: states.hovered ? "pointer" : "default",
          margin: 5,
          padding: 10,
          decorator: dc
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

      style: function() {
        return {
          show: "label",
          font: "bold",
          textColor: "darkgray-dark",
          allowGrowX: true,
          decorator: "gosa-workflow-category",
          padding: 4,
          marginBottom: 6
        }
      }
    },

    "gosa-workflow-category/label": {
      style: function() {
        return {
          textColor: "darkgray-dark"
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
          font: "Subtitle"
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

    "edit-tabview-page": "tabview-page",
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

    "settings-view": "gosa-tabview-page",
    "settings-view/splitpane": "splitpane",
    "settings-view/list-title": {
      style: function() {
        return {
          padding: [8, 20],
          allowGrowX: true,
          decorator: "panel-title"
        };
      }
    },
    "settings-view/list": {
      include: "list",
      alias: "list",
      style: function() {
        return {
          decorator: "panel-body",
          padding: 0
        };
      }
    },

    "settings-view/content": {},
    "settings-view/container": {
      style: function() {
        return {
          decorator: "panel"
        };
      }
    },

    "webhook-editor": {},

    "webhook-editor/title": {
      style: function() {
        return {
          padding: [8, 20],
          allowGrowX: true,
          backgroundColor: "lightgray-dark"
        };
      }
    },

    "webhook-editor/table": {
      include: "table",
      alias: "table",
      style: function() {
        return {
          decorator: "table",
          margin: 6
        };
      }
    },

    "webhook-editor/delete-button": "icon-menu-button",
    "webhook-editor/open-button": "icon-menu-button",
    "webhook-editor/create-button": "icon-menu-button",
    "webhook-editor/action-menu-button": "toolbar-menubutton",

    "webhook-editor/toolbar": {
      style: function() {
        return {
          margin: 8
        }
      }
    },

    "settings-editor/title": {
      style: function() {
        return {
          padding: [8, 20],
          allowGrowX: true,
          backgroundColor: "lightgray-dark"
        };
      }
    },

    "settings-editor": {
    },

    "settings-editor/table": {
      include: "table",
      alias: "table",
      style: function() {
        return {
          decorator: "table",
          margin: 6
        };
      }
    },

    "settings-editor/filter": {
      include : "textfield",
      alias : "textfield",
      style: function() {
        return {
          margin: 8
        }
      }
    },

    "gosa-listitem-window": {
      include: "listitem",
      alias: "listitem",

      style: function(states) {
        return {
          backgroundColor: states.selected ? "bittersweet-light" : undefined,
          textColor: "white",
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

    "gosa-listitem-webhook": {
      include: "listitem",
      alias: "listitem",
      style: function(states) {
        return {
          textColor: "darkgray-dark",
          decorator: "listitem",
          backgroundColor: states.selected ? "lightgray-light" : "transparent"
        }
      }
    },
    "gosa-listitem-webhook/label": {
      style: function() {
        return {
          font: "bold"
        }
      }
    },
    "gosa-listitem-webhook-group": {
      include : "atom",
      alias : "atom",

      style : function() {
        return {
          font : "Subtitle",
          textColor : "darkgray-dark",
          padding : 4,
          marginBottom : 6
        }
      }
    },

    "gosa-spinner": {
      style: function(states) {
        return {
          textColor: "icon-color",
          backgroundColor: states.blocking ? "rgba(0,0,0,0.1)" : "transparent",
          opacity: 0.5,
          show: "icon",
          size: 30,
          zIndex: 10000,
          center: true
        };
      }
    },

    "gosa-dashboard-widget": {
      style: function(states) {
        var dc = "gosa-dashboard-widget";
        if (states.selected) {
          dc += "-selected";
        }
        else if (states.edit) {
          dc += "-edit";
        }
        return {
          padding: 10,
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

    "gosa-droppable": {
      style: function(states) {
        var dc = states.hovered ? "gosa-droppable-hovered" : "gosa-droppable";
        var height = null;
        if (states.invisible) {
          dc = null;
          height = 0;
        }
        return {
          decorator: dc,
          height: height
        }
      }
    },

    "login-dialog": {
      include: "window",
      alias: "window",
      style: function() {
        return {
          contentPadding: 20,
          icon: "gosa/images/logo.svg"
        };
      }
    },

    "login-dialog/captionbar": {
      style: function() {
        return {
          padding: [4, 0, 4, 4],
          textColor: "white",
          backgroundColor: "bittersweet-dark",
          height: 40
        };
      }
    },

    "login-dialog/title": {
      style: function() {
        return {
          paddingLeft: 4,
          font: "Logo"
        };
      }
    },

    "login-dialog/icon": {
      style: function() {
        return {
          scale: true,
          height: 35
        };
      }
    },

    "gosa-dialog-uploadppd" : {
      include : "window",
      alias : "window",
      style : function () {
        return {
          width : 300
        };
      }
    },

    "gosa-table-widget": {},

    "gosa-table-widget/control-bar": {
      style: function() {
        return {
          decorator: "control-bar"
        };
      }
    },

    "gosa-table-widget/add-button": "button-link",
    "gosa-table-widget/remove-button": "button-link",

    "dashboard-resize-frame": {
      style: function() {
        return {
          decorator: "gosa-dashboard-widget-resize"
        };
      }
    },

    "tree-folder" :
    {
      style : function(states)
      {
        var backgroundColor;
        if (states.selected) {
          backgroundColor = "background-selected";
          if (states.disabled) {
            backgroundColor += "-disabled";
          }
        }
        return {
          textColor: states.disabled ? "disabled-text" : null,
          padding : [2, 8, 2, 5],
          icon : states.opened ? "icon/16/places/folder-open.png" : "icon/16/places/folder.png",
          backgroundColor : backgroundColor,
          iconOpened : "icon/16/places/folder-open.png",
          opacity : states.drag ? 0.5 : undefined
        };
      }
    },

    "workflow-wizard" : {},
    "workflow-wizard/next-button" : "button-primary",
    "workflow-wizard/sidebar" : {
      style: function() {
        return {
          decorator : "panel",
          padding : 8
        };
      }
    },

    "progress-item" : {},

    "progress-item/right-container" : {
      style: function() {
        return {
          maxWidth : 250,
          paddingLeft : 8
        };
      }
    },

    "progress-item/line" : {
      style: function(states) {
        return {
          decorator : states.last ? undefined : "vertical-line",
          marginTop : 8,
          marginBottom : 8,
          maxWidth : 12,
          height : 30,
          allowGrowY : true
        };
      }
    },

    "progress-item/indicator" : {
      style: function(states) {
        return {
          decorator : "indicator",
          backgroundColor : (states.active || states.done) ? "aqua-light" : "mediumgray-light",
          textColor: "white",
          width : 24,
          height : 24,
          center : true
        };
      }
    },

    "progress-item/title" : {
      style: function() {
        return {
          paddingTop: 2,
          font : "bold"
        };
      }
    },

    "progress-item/description" : {
      style: function() {
        return {
          paddingTop: 8,
          paddingBottom: 12
        };
      }
    },

    "window/base-selector/tree": "virtual-tree",

    // - FLAT - do not insert anything behind this marker -----------------------------------------------------

    "root": {
      style: function() {
        return {
          backgroundColor: "lightgray-light",
          textColor: "darkgray-dark",
          font: "default"
        };
      }
    },

    "window": {
      style: function(states) {
        var decorator = "window";

        if (states.maximized) {
          decorator = "window-maximized";
        }
        else if (!states.active) {
          decorator = "window-inactive";
        }

        return {
          decorator: decorator,
          contentPadding: [10, 10, 10, 10],
          margin: states.maximized ? 0 : [0, 5, 5, 0]
        };
      }
    },

    "window/captionbar": {
      style: function(states) {
        return {
          decorator: (states.active ? "window-captionbar-active" : "window-captionbar-inactive"),
          textColor: states.active ? "darkgray-dark" : "darkgray-light",
          padding: 10
        };
      }
    },

    "window/icon": {
      style: function() {
        return {
          scale: true,
          width: 22,
          height: 22
        };
      }
    },

    "window/title": {
      style: function() {
        return {
          font: "bold"
        };
      }
    },

    "window-warning": {
      include: "window",
      style: function() {
        return {
          decorator: "window-warning",
          textColor: "#8a6d3b"
        };
      }
    },

    "window-warning/captionbar": {
      include: "window/captionbar",
      style: function() {
        return {
          decorator: "window-warning-captionbar-active",
          textColor: "#8a6d3b"
        };
      }
    },

    "window-warning/title": "window/title",

    "window-error": {
      include: "window",
      style: function() {
        return {
          decorator: "window-error",
          textColor: "#a94442"
        };
      }
    },

    "window-error/captionbar": {
      include: "window/captionbar",
      style: function() {
        return {
          decorator: "window-error-captionbar-active",
          textColor: "#a94442"
        };
      }
    },

    "window-error/title": "window/title",

    "gosa-dialog-register-webhook": "window",
    "gosa-dialog-register-webhook/name-field": "textfield",
    "gosa-dialog-register-webhook/mime-type": "selectbox",
    "gosa-dialog-register-webhook/save-button": "button-primary",
    "gosa-dialog-register-webhook/cancel-button": "button",
    "gosa-dialog-register-webhook/error-message": {
      include: "statusLabel",
      alias: "statusLabel",

      style: function() {
        return {
          padding : 10,
          maxWidth: 350
        }
      }
    },

    "button": {
      style: function(states) {
        var styles = {
          decorator: "button-default",
          textColor: "darkgray-dark",
          padding: [6, 12],
          opacity: undefined,
          font: "default",
          center: true
        };

        if (states.disabled) {
          styles.opacity = 0.45;
        }
        else if (states.hovered || states.pressed) {
          styles.decorator = states.pressed ? "button-default-pressed" : "button-default-focused";
        }

        return styles;
      }
    },

    "button-normal": {
      include: "button",
      style: function(states) {
        var styles = {};

        if (!states.disabled) {
          styles.textColor = "white";
          styles.decorator = "button-normal";
        }

        if (!states.disabled && (states.hovered || states.pressed)) {
          styles.decorator = states.pressed ? "button-normal-pressed" : "button-normal-focused";
        }

        return styles;
      }
    },

    "button-link": {
      include: "button",
      style: function(states) {
        var styles = {
          decorator: "button-link"
        };
        if (!states.disabled && (states.hovered || states.pressed)) {
          styles.decorator = states.pressed ? "button-normal-pressed" : "button-normal-focused";
        }
        return styles;
      }
    },

    "button-default": "button",

    "button-primary": {
      include: "button",
      style: function(states) {
        var styles = {};

        if (!states.disabled) {
          styles.textColor = "white";
          styles.decorator = "button-primary";
        }

        if (!states.disabled && (states.hovered || states.pressed)) {
          styles.decorator = states.pressed ? "button-primary-pressed" : "button-primary-focused";
        }
        return styles;
      }
    },

    "button-success": {
      include: "button",
      style: function(states) {
        var styles = {};

        if (!states.disabled) {
          styles.textColor = "white";
          styles.decorator = "button-success";
        }

        if (!states.disabled && (states.hovered || states.pressed)) {
          styles.decorator = states.pressed ? "button-success-pressed" : "button-success-focused";
        }
        return styles;
      }
    },

    "button-info": {
      include: "button",
      style: function(states) {
        var styles = {};

        if (!states.disabled) {
          styles.textColor = "white";
          styles.decorator = "button-info";
        }

        if (!states.disabled && (states.hovered || states.pressed)) {
          styles.decorator = states.pressed ? "button-info-pressed" : "button-info-focused";
        }
        return styles;
      }
    },

    "button-warning": {
      include: "button",
      style: function(states) {
        var styles = {};

        if (!states.disabled) {
          styles.textColor = "white";
          styles.decorator = "button-warning";
        }

        if (!states.disabled && (states.hovered || states.pressed)) {
          styles.decorator = states.pressed ? "button-warning-pressed" : "button-warning-focused";
        }
        return styles;
      }
    },

    "button-warning/icon": {
      style: function() {
        return {
          width: 22,
          scale: true
        };
      }
    },

    "button-danger": {
      include: "button",
      style: function(states) {
        var styles = {};

        if (!states.disabled) {
          styles.textColor = "white";
          styles.decorator = "button-danger";
        }

        if (!states.disabled && (states.hovered || states.pressed)) {
          styles.decorator = states.pressed ? "button-danger-pressed" : "button-danger-focused";
        }
        return styles;
      }
    },

    "button-danger/icon": "button-warning/icon",
    "button-info/icon": "button-warning/icon",
    "button-normal/icon": "button-warning/icon",

    "textfield": {
      style: function(states) {
        var decorator;

        var focused = !!states.focused;
        var invalid = !!states.invalid;
        var disabled = !!states.disabled;

        if (focused && invalid && !disabled) {
          decorator = "textfield-invalid";
        }
        else if (focused && !invalid && !disabled) {
          decorator = "textfield-focused";
        }
        else if (disabled) {
          decorator = "textfield-disabled";
        }
        else if (!focused && invalid && !disabled) {
          decorator = "textfield-invalid";
        }
        else {
          decorator = "textfield-normal";
        }

        var textColor;
        if (states.disabled) {
          decorator = "textfield-disabled";
          textColor = "mediumgray-dark";
        }
        else if (states.showingPlaceholder) {
          textColor = "lightgray-dark";
        }
        else {
          textColor = "darkgray-dark";
        }

        return {
          decorator: decorator,
          padding: [6, 12],
          textColor: textColor
        };
      }
    },

    "menu": {
      style: function(states) {
        var result = {
          decorator: "menu",
          spacingX: 6,
          spacingY: 0,
          padding: [4, 0, 4, 0],
          iconColumnWidth: 16,
          arrowColumnWidth: 4,
          placementModeY: states.submenu || states.contextmenu ? "best-fit" : "keep-align"
        };

        if (states.submenu) {
          result.position = "right-top";
          result.offset = [-2, -3];
        }

        return result;
      }
    },

    "menu-separator": {
      style: function() {
        return {
          height: 0,
          decorator: "menu-separator",
          margin: [4, 2]
        };
      }
    },

    "menu-button": {
      alias: "atom",

      style: function(states) {
        return {
          textColor: states.disabled ? "darkgray-light" : "white",
          backgroundColor: states.selected ? "darkgray-light" : undefined,
          padding: [5, 18]
        };
      }
    },

    "menu-button/label": {
      style: function() {
        return {
          paddingRight: 6
        };
      }
    },

    "menu-button/arrow": {
      style: function() {
        return {
          source: "@Ligature/next",
          scale: true,
          width: 10,
          height: 10
        };
      }
    },

    "scrollbar": {
      style: function() {
        return {
          backgroundColor: "lightgray-light"
        };
      }
    },

    "scrollbar/slider/knob": {
      style: function(states) {
        var decorator = "scroll-knob";

        if (!states.disabled) {
          if (states.hovered && !states.pressed && !states.checked) {
            decorator = "scroll-knob-hovered";
          }
          else if (states.hovered && (states.pressed || states.checked)) {
            decorator = "scroll-knob-pressed";
          }
          else if (states.pressed || states.checked) {
            decorator = "scroll-knob-pressed";
          }
        }

        return {
          height: 8,
          width: 8,
          cursor: states.disabled ? undefined : "pointer",
          decorator: decorator,
          minHeight: states.horizontal ? undefined : 9,
          minWidth: states.horizontal ? 9 : undefined
        };
      }
    },

    "scrollbar/button": {
      style: function() {
        return {
          width: 0,
          height: 0,
          icon: undefined,
          margin: 0
        };
      }
    },

    "checkbox": {
      alias: "atom",

      style: function(states) {
        var icon = "@Ligature/check";
        if (states.undetermined) {
          icon = "@Ligature/minus";
        }

        return {
          icon: icon,
          minWidth: 20,
          gap: 8
        };
      }
    },

    "checkbox/icon": {
      style: function(states) {
        var decorator;

        if (states.disabled) {
          decorator = "checkbox-disabled";
        }
        else if (states.focused && states.hovered) {
          decorator = "checkbox-hovered";
        }
        else {
          decorator = "checkbox";
        }

        decorator += states.checked ? "-checked" : "";
        if (!states.disabled) {
          decorator += states.invalid && !states.disabled ? "-invalid" : "";
        }

        return {
          textColor: "white",
          decorator: decorator,
          width: 16,
          scale: true
        };
      }
    },

    "selectbox": {
      alias: "atom",

      style: function(states) {
        var decorator = "selectbox-field";
        var padding = [6, 12];

        if (states.disabled) {
          decorator = "selectbox-field-disabled";
        }
        else if (states.focused || states.pressed) {
          decorator = "selectbox-field-focused";
        }

        if (states.invalid && !states.disabled) {
          decorator += "-invalid";
        }

        return {
          decorator: decorator,
          padding: padding
        };
      }
    },

    "selectbox/list": {
      alias: "list",
      style: function() {
        return {};
      }
    },

    "selectbox/popup": {
      style: function() {
        return {
          decorator: "popup",
          backgroundColor: "white"
        };
      }
    },

    "tabview-page": {
      alias: "widget",
      include: "widget",

      style: function() {
        return {
          padding: 8
        };
      }
    },

    "listitem": {
      alias: "atom",

      style: function(states) {
        return {
          padding: [5, 20],
          textColor: states.selected ? "white" : "darkgray-dark",
          decorator: states.selected ? "listitem-selected" : "listitem",
          opacity: states.drag ? 0.5 : undefined
        };
      }
    },

    "spinner": {
      style: function(states) {
        var decorator;

        var focused = !!states.focused;
        var invalid = !!states.invalid;
        var disabled = !!states.disabled;

        if (focused && invalid && !disabled) {
          decorator = "textfield-invalid";
        }
        else if (focused && !invalid && !disabled) {
          decorator = "textfield-focused";
        }
        else if (disabled) {
          decorator = "textfield-disabled";
        }
        else if (!focused && invalid && !disabled) {
          decorator = "textfield-invalid";
        }
        else {
          decorator = "textfield-normal";
        }

        return {
          decorator: decorator
        };
      }
    },

    "spinner/textfield": {
      style: function(states) {
        return {
          padding: [5, 10],
          textColor: states.disabled ? "mediumgray-dark" : "darkgray-dark"
        };
      }
    },

    "spinner/upbutton": {
      style: function(states) {
        var decorator = "spinner-button";

        if (states.disabled) {
          decorator = undefined;
        }
        else if (states.focused) {
          decorator = "spinner-button-focused";
        }

        return {
          textColor: states.disabled ? "lightgray-dark" : "darkgray-light",
          padding: [0, 4, 0, 4],
          backgroundColor: states.hovered ? "mediumgray-light" : "transparent",
          decorator: decorator,
          icon: "@Ligature/up",
          margin: 0
        };
      }
    },

    "spinner/upbutton/icon": {
      style: function() {
        return {
          height: 10,
          scale: true
        };
      }
    },

    "spinner/downbutton": {
      include: "spinner/upbutton",
      style: function() {
        return {
          icon: "@Ligature/down"
        };
      }
    },

    "spinner/downbutton/icon": "spinner/upbutton/icon",

    "tooltip": {
      include: "popup",

      style: function(states) {
        return {
          decorator: "tooltip",
          backgroundColor: states.invalid ? "grapefruit-dark" : "darkgray-dark",
          textColor: "white",
          padding: [6, 10],
          offset: [15, 5, 5, 5]
        };
      }
    },

    "virtual-tree": {
      include: "tree",
      alias: "tree",

      style: function() {
        return {
          padding: 1,
          minWidth: 260
        };
      }
    },

    "splitpane/splitter": {
      style: function(states) {
        return {
          width: states.horizontal ? 3 : undefined,
          height: states.vertical ? 3 : undefined,
          padding: 3,
          backgroundColor: "white"
        };
      }
    },

    "splitpane/slider": {
      style: function(states) {
        return {
          width: states.horizontal ? 3 : undefined,
          height: states.vertical ? 3 : undefined,
          backgroundColor: "white"
        };
      }
    },

    "toolbar/part": {},
    "toolbar/part/container": {},
    "toolbar/part/handle": {},

    "toolbar-button": {
      alias: "atom",

      style: function(states) {
        var backgroundColor = "transparent";
        var textColor = "darkgray-dark";

        if (states.disabled) {
          textColor = "lightgray-dark";
        }
        else if (states.hovered && !states.pressed && !states.checked) {
          backgroundColor = "lightgray-dark";
        }
        else if (states.hovered && (states.pressed || states.checked)) {
          backgroundColor = "mediumgray-light";
        }
        else if (states.pressed || states.checked) {
          backgroundColor = "mediumgray-dark";
        }

        return {
          cursor: states.disabled ? undefined : "pointer",
          backgroundColor: backgroundColor,
          textColor: textColor,
          padding: [3, 10]
        };
      }
    },

    "toolbar-menubutton/arrow": {
      alias: "image",
      include: "image",

      style: function(states) {
        return {
          source: "@Ligature/dropdown/12",
          cursor: states.disabled ? undefined : "pointer",
          marginLeft: 2
        };
      }
    },

    "menu-checkbox": {
      alias: "menu-button",
      include: "menu-button",

      style: function(states) {
        return {
          icon: !states.checked ? undefined : "@Ligature/check/16",
          textColor: "lightgray-light"
        };
      }
    },

    "table-scroller/header": {
      style: function() {
        return {
          decorator: "table-header"
        };
      }
    },

    "table-header-cell": {
      alias: "atom",

      style: function(states) {
        return {
          decorator: states.first ? "table-header-cell-first" : "table-header-cell",
          minWidth: 13,
          font: "bold",
          cursor: states.disabled ? undefined : "pointer",
          padding: 8,
          sortIcon: states.sorted ? (
          states.sortedAscending ? "@Ligature/down/12" : "@Ligature/up/12"
          ) : undefined
        };
      }
    },

    "table-header-cell/sort-icon": {
      style: function() {
        return {
          alignY: "middle",
          alignX: "right"
        };
      }
    },

    "bread-crumb": {
      style: function() {
        return {
          minHeight: 38,
          backgroundColor: "lightgray-dark",
          decorator: "bread-crumb"
        };
      }
    },

    "bread-crumb-item": {
      style: function(states) {
        return {
          padding: 0,
          margin: 0,
          backgroundColor: states.forelast || states.last ? "transparent" : (
          states.nextpressed ? "aqua-light" : "aqua-dark")
        };
      }
    },

    "bread-crumb-item/atom": {
      include: "atom",
      alias: "atom",
      style: function(states) {
        var background = "aqua-dark";

        if (states.last) {
          background = "transparent";
        }
        else if (states.hovered) {
          background = "aqua-light";
        }

        return {
          paddingLeft: 6,
          paddingRight: 6,
          backgroundColor: background,
          textColor: states.last ? "darkgray-dark" : "white"
        };
      }
    },

    "bread-crumb-item/atom/icon": {
      style: function() {
        return {
          width: 22,
          height: 22,
          scale: true
        };
      }
    },

    "bread-crumb-item/arrow": {
      style: function(states) {
        return {
          height: 0,
          width: 0,
          decorator: states.last ? undefined : "bread-crumb-item-arrow"
        };
      }
    },

    "bread-crumb-item/arrow-inner": {
      style: function(states) {
        return {
          height: 0,
          width: 0,
          decorator: states.last ? undefined : (
          states.hovered ? "bread-crumb-item-arrow-inner-pressed" : "bread-crumb-item-arrow-inner" )
        };
      }
    },

    "datechooser" :
    {
      style : function()
      {
        return {
          backgroundColor : "white",
          decorator : "popup",
          minWidth: 220
        };
      }
    },

    "datechooser/navigation-bar" :
    {
      style : function(states)
      {
        return {
          backgroundColor : undefined,
          textColor : states.disabled ? "text-disabled" : states.invalid ? "invalid" : undefined,
          padding : [4, 10]
        };
      }
    },


    "datechooser/button" :
    {
      style : function(states)
      {
        var result = {
          show   : "icon",
          cursor : states.disabled ? undefined : "pointer"
        };

        if (states.lastYear) {
          result.icon = qx.theme.simple.Image.URLS["arrow-rewind"];
        } else if (states.lastMonth) {
          result.icon = qx.theme.simple.Image.URLS["arrow-left"];
        } else if (states.nextYear) {
          result.icon = qx.theme.simple.Image.URLS["arrow-forward"];
        } else if (states.nextMonth) {
          result.icon = qx.theme.simple.Image.URLS["arrow-right"];
        }

        return result;
      }
    }

    // Do NOT place any appearances here, that are not FLAT theme related. Put them above
    // the marker above.
  }
});
