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

/**
* Element that is used to display the wizard progress.
*/
qx.Class.define("gosa.ui.form.ProgressItem", {
  extend : qx.ui.core.Widget,
  
  construct : function(index, title, description) {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.HBox());

    this.setIndex(index);
    this.setTitle(title);
    this.setDescription(description);
    this._createChildControl("line");

    this.initActive();
    this.initDone();
  },
    
  properties : {
    // overridden
    appearance: {
      refine: true,
      init: "progress-item"
    },

    index: {
      init : null,
      check: "Integer",
      apply: "_applyIndex"
    },

    title: {
      init : null,
      check: "String",
      apply: "_applyTitle"
    },

    description: {
      init : null,
      check: "String",
      apply: "_applyDescription"
    },

    active: {
      init : false,
      check: "Boolean",
      apply: "_applyActive"
    },

    done: {
      init : false,
      check: "Boolean",
      apply: "_applyDone"
    }
  },
    
  members : {
    // overridden
    /**
     * @lint ignoreReferenceField(_forwardStates)
     */
    _forwardStates : {
      last : true,
      active : true,
      done : true
    },

    // property apply
    _applyIndex : function(value)
    {
      this.getChildControl("indicator").setLabel("" + value);
    },

    // property apply
    _applyTitle : function(value)
    {
      this.getChildControl("title").setValue(value);
    },

    // property apply
    _applyDescription : function(value)
    {
      this.getChildControl("description").setValue(value);
    },

    // property apply
    _applyDone : function(value)
    {
      if (value) {
        this.getChildControl("indicator").setShow("icon");
        this.addState("done");
      }
      else {
        this.getChildControl("indicator").setShow("label");
        this.removeState("done");
      }
    },

    // property apply
    _applyActive : function(value)
    {
      if (value) {
        this.getChildControl("description").show();
        this.addState("active");
      }
      else {
        this.getChildControl("description").exclude();
        this.removeState("active");
      }
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "left-container":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this._addAt(control, 0);
          break;

        case "indicator":
          control = new qx.ui.basic.Atom(null, "@Ligature/check/12");
          this.getChildControl("left-container").addAt(control, 0);
          break;

        case "line":
          control = new qx.ui.core.Widget();
          this.getChildControl("left-container").addAt(control, 1, {flex: 1});
          break;

        case "right-container":
          control = new qx.ui.container.Composite(new qx.ui.layout.VBox());
          this._addAt(control, 1, {flex: 1});
          break;

        case "title":
          control = new qx.ui.basic.Label();
          this.getChildControl("right-container").addAt(control, 0);
          break;

        case "description":
          control = new qx.ui.basic.Label();
          control.setRich(true);
          control.setWrap(true);
          this.getChildControl("right-container").addAt(control, 1, {flex: 1});
          break;
      }

      return control || this.base(arguments, id);
    }
  }
});
