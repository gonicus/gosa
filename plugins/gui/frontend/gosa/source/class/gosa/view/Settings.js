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
    this._createChildControl("list-title");
    this._createChildControl("list");
    this._createChildControl("container");
    this.setLayout(new qx.ui.layout.Canvas());
  },

  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */
  properties : {
    appearance: {
      refine: true,
      init: "settings-view"
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
          control.setSelectionMode("one");
          this.__initEditorList(control);
          this.getChildControl("list-content").add(control, {flex: 1});
          break;

        case "list-title":
          control = new qx.ui.basic.Label(this.tr("Sections"));
          this.getChildControl("list-content").add(control);
          break;

        case "container":
          control = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
          control.add(this.getChildControl("content"), { edge: 0 });
          this.getChildControl("splitpane").add(control, 2);
          break;

        case "splitpane":
          control = new qx.ui.splitpane.Pane("horizontal");
          this.add(control, {edge : 0});
          break;

        case "content":
          control = new qx.ui.container.Stack();
          this.getChildControl("splitpane").add(control, 2);
          break;

        case "list-content":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this.getChildControl("splitpane").add(control, 1);
          break;
      }

      return control || this.base(arguments, id);
    },


    __initEditorList: function(list) {
      list.setLabelPath("name");
      list.setDelegate({

        configureItem: function(item) {
          item.setHeight(50);
        },

        sorter: function(a, b) {
          return a.getName().localeCompare(b.getName());
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
