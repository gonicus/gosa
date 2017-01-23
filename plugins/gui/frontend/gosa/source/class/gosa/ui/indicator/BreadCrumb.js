/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.indicator.BreadCrumb", {
  extend: qx.ui.core.Widget,

  construct: function() {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.HBox());
  },

  events : {
    "selected" : "qx.event.type.Data"
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
    _itemSelected : function(data)
    {
      this.fireDataEvent("selected", data);
    },

    _applyPath : function(data) {
      var children = this._getChildren();
      var item;
      var precedingItem;

      for (var i=0; i<data.length; i++) {
        if (!!children[i]) {
          item = children[i];
          item.show();
        }
        else {
          item = new gosa.ui.indicator.BreadCrumbItem(this._itemSelected, this);
          this._add(item);
        }

        item.setModel(data[i]);

        item.removeState("forelast");
        item.removeState("last");

        if (precedingItem)  {
          item.setPreceding(precedingItem);
        }

        precedingItem = item;
      }

      if (data.length) {
        children = this._getChildren();
        if (data.length > 1) {
          children[data.length - 2].addState("forelast");
        }
        children[data.length - 1].addState("last");
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
