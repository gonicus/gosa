/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.BreadCrumbItem", {
  extend: qx.ui.core.Widget,

  construct: function() {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.HBox());

    this._createChildControl("atom");
    this._arrowContainer = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
    this._add(this._arrowContainer);
    this._createChildControl("arrow");
    this._createChildControl("arrow-inner");
  },

  properties: {
    //overridden
    appearance: {
      refine: true,
      init: "bread-crumb-item"
    },

    label : {
      init: null,
      check: "String",
      event : "changeLabel",
      nullable: true
    },

    icon : {
      init: null,
      check: "String",
      event : "changeIcon",
      nullable: true
    }
  },

  members: {
    // overidden
    _forwardStates : {
      last : true,
      forelast : true
    },

    // overidden
    _createChildControlImpl : function(id, hash)
    {
      var control = null;

      switch(id)
      {
        case "atom":
          control = new qx.ui.basic.Atom();
          this.bind("label", control, "label");
          this.bind("icon", control, "icon");
          this._add(control);
          break;

        case "arrow":
          control = new qx.ui.core.Widget();
          this._arrowContainer.add(control, {top: 0, left: 1, right: 0, bottom: 0});
          break;

        case "arrow-inner":
          control = new qx.ui.core.Widget();
          this._arrowContainer.add(control, {top: 0, left: 0, right: 1, bottom: 0});
          break;
      }

      return control || this.base(arguments, id, hash);
    }
  },

  destruct : function()
  {
    this._disposeObjects("_arrowContainer");
  }
});
