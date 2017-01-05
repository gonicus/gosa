/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.SearchAid",
{
  extend : qx.ui.container.Composite,

  construct : function() {
    // Call super class and configure ourselfs
    this.base(arguments);
    this.setLayout(new qx.ui.layout.VBox(10, "top"));

    this.__selection = {};
    this.__filters = {};
    this.__block_event = false;
  },

  events: {
    "filterChanged" : "qx.event.type.Data"
  },

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */

  members :
  {
    __selection : null,
    __filters : null,
    __block_event: false,

    getSelection : function() {
      return this.__selection;
    },

    addFilter : function(title, cat, elements, dflt){
      var w = new qx.ui.groupbox.GroupBox(title);
      this.__filters[cat] = {"default": dflt};

      if (!title) {
        w.getChildControl("legend").exclude();
        w.getChildControl("frame").setMarginTop(0);
        w.getChildControl("frame").setPaddingTop(0);
      }

      w.setAppearance("SearchAid");
      w.setLayout(new qx.ui.layout.VBox(0));

      var group = new qx.ui.form.RadioGroup();

      for (var k in elements) {
        var v = elements[k];
        var b = new qx.ui.form.ToggleButton(v.name+" ("+v.count+")");

        if (!this.__selection[cat]) {
          this.__selection[cat] = dflt;
        }

        b.setAppearance("SearchAidButton");
        b.setUserData("category", k);
        w.add(b);
        group.add(b);

          // Set activated by default
          if (k == this.__selection[cat]) {
            group.setSelection([b]);
          }
	    }
	    
	    group.addListener("changeSelection", function() {
        if (this.__block_event) {
          return;
        }
        var selection = group.getSelection()[0].getUserData("category");
        if (this.__selection[cat] != selection) {
          this.__selection[cat] = selection;
          this.fireDataEvent("filterChanged", {
            "category": cat,
            "selection": selection
          });
        }
      }, this);

      this.__filters[cat]['widget'] = w;
	    this.__filters[cat]['group'] = group;
	    this.__filters[cat]['default'] = dflt;
	    this.add(w);
	  },

    updateFilter : function (cat, elements) {
      this.__block_event = true;
      var w = this.__filters[cat]['widget'];
      var group = this.__filters[cat]['group'];

      // Remove old members
      w.removeAll();
      var children = group.getChildren();
      for (var i in children) {
        group.remove(children[i]);
      }

      // Add replacement members
      for (var k in elements) {
        var v = elements[k];
        var b = new qx.ui.form.ToggleButton(v.name+" ("+v.count+")");

        b.setAppearance("SearchAidButton");
        b.setUserData("category", k);
        w.add(b);
        group.add(b);

        // Set selection
        if (k == this.__selection[cat]) {
          group.setSelection([b]);
        }
      }
      this.__block_event = false;
    },

    hasFilter : function() {
      return !qx.lang.Object.isEmpty(this.__filters);
    },

    resetSelection : function(which) {
      if (which) {
        this.__selection[which] = this.__filters[which]["default"];
      } else {
        for (var cat in this.__filters) {
          this.__selection[cat] = this.__filters[cat]["default"];
        }
      }
    }

  }
});
