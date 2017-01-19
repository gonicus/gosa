/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.BreadCrumb", {
  extend: qx.ui.core.Widget,

  construct: function() {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.HBox());
  },

  properties: {
    //overridden
    appearance: {
      refine: true,
      init: "bread-crumb"
    },

    path : {
      init: null,
      check: "Array",
      nullable: true,
      apply: "_applyPath"
    }
  },

  members: {

    _applyPath : function(data) {
      var children = this._getChildren();
      var item;

      for (var i=0; i<data.length; i++) {
        if (!!children[i]) {
          item = children[i];
          item.show();
        }
        else {
          item = new gosa.ui.BreadCrumbItem();
          this._add(item);
        }

        item.set({
          label : data[i][1],
          icon : data[i][0]
        });

        item.removeState("forelast");
        item.removeState("last");
      }

      if (data.length) {
        if (data.length > 1) {
          this._getChildren()[data.length - 2].addState("forelast");
        }
        this._getChildren()[data.length - 1].addState("last");
      }

      for (i=data.length;i<children.length; i++) {
        children[i].exclude();
      }
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
  }
});
