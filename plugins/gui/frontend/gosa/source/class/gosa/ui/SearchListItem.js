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

/*
#asset(gosa/*)
*/

/**
 * @lint ignoreUndefined(getThrobber)
 */
qx.Class.define("gosa.ui.SearchListItem", {

  extend: qx.ui.core.Widget,
  implement : [qx.ui.form.IModel],
  include : [qx.ui.form.MModelProperty],

  construct: function(){
    this.base(arguments);

    this.setSelectable(false);
    this._setLayout(new qx.ui.layout.Canvas());
  },

  events: {
    "edit": "qx.event.type.Data",
    "remove": "qx.event.type.Data"
  },

  properties: {
    appearance: {
      refine: true,
      init: "search-list-item"
    },

    dn :
    {
      apply : "_applyDn",
      nullable : true,
      check : "String",
      event : "changeDn"
    },

    uuid :
    {
      nullable : true,
      check : "String",
      apply: "reset",
      event : "changeUuid"
    },

    description :
    {
      apply : "_applyDescription",
      nullable : true,
      check : "String",
      event : "changeDescription"
    },

    icon :
    {
      apply : "_applyIcon",
      nullable : true,
      check : "String",
      event : "changeIcon"
    },

    title :
    {
      apply : "_applyTitle",
      nullable : true,
      check : "String",
      event : "changeTitle"
    },

    gap :
    {
      check : "Integer",
      nullable : false,
      event : "changeGap",
      themeable : true,
      init : 0
    },

    type : {
      check: "String",
      nullable: true
    },

    isLoading :
    {
      check : "Boolean",
      nullable : false,
      apply: "_applyIsLoading",
      event : "changeIsLoading",
      init : false
    },

    toolbarEnabled: {
      check: "Boolean",
      init: true
    }
  },

  members: {

    reset: function(){
      if(this.isIsLoading()){
        this.setIsLoading(false);
      }
      this._onMouseOut();
    },

    /* Applies the loading state and toggles the
     * spinner accordingly
     * */
    _applyIsLoading: function(value){
      if (value) {
        this.getChildControl("throbber").show();
      } else {
        this.getChildControl("throbber").exclude();
      }
    },

    /**
     * @lint ignoreReferenceField(_forwardStates)
     */
    _forwardStates: {
      focused : false,
      hovered : false,
      selected : false,
      dragover : false
    },

    _onMouseOver : function() {
      this.addState("hovered");
      if (this.isToolbarEnabled()) {
        this.getChildControl("toolbar").show();
      }
    },

    _onMouseOut : function() {
      this.removeState("hovered");
      if (this.isToolbarEnabled()) {
        this.getChildControl("toolbar").hide();
      }
    },

    _applyTitle: function(value){
      this._showChildControl("title");
      var widget = this.getChildControl("title");
      if(widget){
        widget.setValue(value);
      }
    },

    _applyIcon: function(value){
      var widget = this.getChildControl("icon");
      if (value) {
        new qx.util.DeferredCall(function() {
          widget.setSource(value);
        }, this).schedule();
        this._showChildControl("icon");
      } else {
        this._excludeChildControl("icon");
      }
    },

    _applyDescription: function(value){
      var widget = this.getChildControl("description");
      if(widget){
        widget.setValue(value);
      }
    },

    _applyDn: function(value){
      var widget = this.getChildControl("dn");
      if(widget){
        widget.setValue(value);
      }
    },

    // overidden
    _createChildControlImpl : function(id, hash)
    {
      var control = null;

      switch(id)
      {
        case "container":
          // Create a grid layout to be able to place elements in order
          var layout = new qx.ui.layout.Grid();
          layout.setColumnFlex(1, 2);
          layout.setRowFlex(2, 2);
          layout.setSpacing(0);
          control = new qx.ui.container.Composite(layout);
          this._add(control, {top:0, left:0, right:0, bottom:0});
          break;
        
        case "toolbar":
          // create and add Part 3 to the toolbar
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(0));
          var Button1 = new qx.ui.form.Button(null, "@Ligature/edit");
          Button1.getChildControl("icon").set({width: 22, scale: true});
          Button1.setAppearance("button-link");
          Button1.setAllowGrowY(false);
          var Button2 = new qx.ui.form.Button(null, "@Ligature/trash");
          Button2.setAppearance("button-link");
          Button2.setAllowGrowY(false);
          Button2.getChildControl("icon").set({width: 22, scale: true});
          control.add(Button1);
          control.add(Button2);
          control.setAllowGrowY(false);
          control.setAllowGrowX(false);
          this.getChildControl("container").add(control, {row: 0, column: 2, rowSpan: 3});

          Button1.addListener("execute", function(){
            this.fireDataEvent("edit", this.getModel());
          }, this);

          Button2.addListener("execute", function(){
            this.fireDataEvent("remove", this.getModel());
          }, this);

          // Hide the toolbar as default
          control.hide();
          this.addListener("mouseover", this._onMouseOver, this);
          this.addListener("mouseout", this._onMouseOut, this);
          break;
        
        case "throbber":
          // Append the throbber
          control = new gosa.ui.Throbber();
          this._add(control, {top: 0, left:0, right: 0, bottom: 0});
          break;

        case "icon":
          control = new qx.ui.basic.Image();
          control.setAnonymous(true);
          this.getChildControl("container").add(control, {row: 0, column: 0, rowSpan: 3});
          break;

        case "title":
          control = new qx.ui.basic.Label("");
          this.getChildControl("container").add(control, {row: 0, column: 1});
          control.addListener("click", function(){
              this.fireDataEvent("edit", this.getModel());
            }, this);
          control.setRich(true);
          break;

        case "dn":
          control = new qx.ui.basic.Label("");
          this.getChildControl("container").add(control, {row: 1, column: 1});
          control.setAnonymous(true); 
          control.setSelectable(true);
          control.setRich(true);
          break;

        case "description":
          control = new qx.ui.basic.Label("");
          control.setAnonymous(true); 
          this.getChildControl("container").add(control, {row: 2, column: 1});
          control.setRich(true);
          control.setSelectable(false);
          break;
      }

      return control || this.base(arguments, id, hash);
    }
  }
});
