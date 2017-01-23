/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.indicator.BreadCrumbItem", {
  extend: qx.ui.core.Widget,

  construct: function(callback, context) {
    this.base(arguments);
    this._callback = callback.bind(context);
    this._setLayout(new qx.ui.layout.HBox());

    this._createChildControl("atom");
    this._arrowContainer = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
    this._add(this._arrowContainer);
    this._createChildControl("arrow");
    this._createChildControl("arrow-inner");

    // Add listeners
    this.addListener("pointerover", this._onPointerOver);
    this.addListener("pointerout", this._onPointerOut);
    this.addListener("pointerup", this._onPointerUp);
  },

  properties: {
    //overridden
    appearance: {
      refine: true,
      init: "bread-crumb-item"
    },

    model : {
      init: null,
      apply: "_applyModel"
    },

    preceding : {
      init: null,
      check: "gosa.ui.indicator.BreadCrumbItem",
      nullable: true
    }
  },

  members: {
    _callback : null,

    // overidden
    /**
     * @lint ignoreReferenceField(_forwardStates)
     */
    _forwardStates : {
      last : true,
      forelast : true,
      hovered : true
    },

    _applyModel : function(value)
    {
      if (value) {
        this.getChildControl("atom").set({
          label : value.getTitle(),
          icon : gosa.util.Icons.getIconByType(value.getType(), 16)
        });
      }
    },

    _onPointerOver : function(e)
    {
      this.addState("hovered");

      if (this.getPreceding()) {
        this.getPreceding().addState("nextpressed");
      }
    },

    _onPointerOut : function(e)
    {
      this.removeState("hovered");

      if (this.getPreceding()) {
        this.getPreceding().removeState("nextpressed");
      }
    },

    _onPointerUp : function()
    {
      this._callback(this.getModel());
    },

    // overidden
    _createChildControlImpl : function(id, hash)
    {
      var control = null;

      switch(id)
      {
        case "atom":
          control = new qx.ui.basic.Atom();
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
    this._callback = null;
  }
});
