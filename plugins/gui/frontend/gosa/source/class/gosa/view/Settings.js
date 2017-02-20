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

/* ************************************************************************

#asset(gosa/*)

************************************************************************ */

qx.Class.define("gosa.view.Settings",
{
  extend : qx.ui.tabview.Page,
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/gear");
    this.getChildControl("button").getChildControl("label").exclude();
    this._createChildControl("list");
    this.setLayout(new qx.ui.layout.HBox());
  },
  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    appearance: {
      refine: true,
      init: "settings-tabview-page"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "list":
          control = new qx.ui.list.List(null);
          this.__initEditorList(control);
          this._addAt(control, 0);
          break;

        case "content":
          control = new qx.ui.container.Stack();
          this._addAt(control, 1, {flex: 1});
          break;
      }

      return control || this.base(arguments, id);
    },


    __initEditorList: function(list) {
      list.setLabelPath("namespace");
      list.setDelegate({

        configureItem: function(item) {
          item.setHeight(50);
        },

        bindItem: function(controller, item, index) {
          controller.bindProperty("", "model", null, item, index);
          controller.bindProperty("namespace", "label", {
            converter: function(value) {
              var parts = value.split(".");
              parts.shift();
              return qx.lang.String.firstUp(parts.join("."));
            }
          }, item, index);
        },

        sorter: function(a, b) {
          return a.getNamespace().localeCompare(b.getNamespace());
        },

        group: function(item) {
          return qx.lang.String.firstUp(item.getNamespace().split(".")[0]);
        }
      });

      this.addListenerOnce("appear", function() {
        list.setModel(gosa.data.SettingsRegistry.getHandlers());
      }, this);

      list.getSelection().addListener("change", function() {
        var selection = list.getSelection().getItem(0);
        var editor = gosa.data.SettingsRegistry.getEditor(selection.getNamespace());
        if (editor) {
          var stack = this.getChildControl("content");
          if (stack.getChildren().indexOf(editor) === -1) {
            stack.add(editor);
          }
          stack.setSelection([editor]);
        }
      }, this);
    }
  }
});
