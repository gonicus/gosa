qx.Class.define("cute.ui.SearchListItem", {

  extend: qx.ui.core.Widget,
  implement : [qx.ui.form.IModel],
  include : [qx.ui.form.MModelProperty],

  construct: function(){
    this.base(arguments);

    this.setMarginBottom(10);

    var layout = new qx.ui.layout.Grid();
    layout.setColumnFlex(1, 2);
    layout.setRowFlex(1, 2);
    layout.setSpacing(0);
    this._setLayout(layout);

    // create and add Part 3 to the toolbar
    var toolbar = new qx.ui.toolbar.ToolBar();
    toolbar.setPadding(0);
    var part = new qx.ui.toolbar.Part();
    var Button1 = new qx.ui.toolbar.Button("Edit");
    var Button2 = new qx.ui.toolbar.Button("Delete");
    var Button3 = new qx.ui.toolbar.Button("Actions");
    part.add(Button1);
    part.add(Button2);
    part.add(Button3);
    toolbar.add(part);
    toolbar.setAllowGrowY(false);
    this._add(toolbar, {row: 0, column: 2, rowSpan: 3});

    Button1.addListener("execute", function(){
        this.fireDataEvent("edit", this.getModel());
      }, this);

    this.addListener("mouseover", this._onMouseOver, this);
    this.addListener("mouseout", this._onMouseOut, this);

    this.setAppearance("SearchListItem");
  },

  events: {
    "edit": "qx.event.type.Data"
  },

  properties: {

    dn :
    {
      apply : "_applyDn",
      nullable : true,
      check : "String",
      event : "changeDn"
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
    }
  },


  members:{

    _onMouseOver : function() {
      this.addState("hovered");
    },

    _onMouseOut : function() {
      this.removeState("hovered");
    },

    _applyTitle: function(value){
      this._showChildControl("title");
      var widget = this.getChildControl("title");
      if(widget){
        widget.setValue(value);
      }
    },

    _applyIcon: function(value){
      this._showChildControl("icon");
      var widget = this.getChildControl("icon");
      if(widget){
        widget.setSource(value);
      }
    },

    _applyDescription: function(value){
      this._showChildControl("description");
      var widget = this.getChildControl("description");
      if(widget){
        widget.setValue(value);
      }
    },

    _applyDn: function(value){
      this._showChildControl("dn");
      var widget = this.getChildControl("dn");
      if(widget){
        widget.setValue(value);
      }
    },

    _createChildControlImpl : function(id, hash)
    {
      var control;

      switch(id)
      {
        case "icon":

          var theme = "default";
          if (cute.Config.theme) {
            theme = cute.Config.theme;
          }

          var path = "cute/themes/" + theme + "/objects/" + this.getIcon(); 
          control = new qx.ui.basic.Image(path);
          control.setHeight(64);
          control.setWidth(64);
          control.setScale(true);
          this._add(control, {row: 0, column: 0, rowSpan: 3});
          break;
        case "title":
          control = new qx.ui.basic.Label(this.getTitle());
          this._add(control, {row: 0, column: 1});
          control.setFont("SearchResultTitle");
          control.setTextColor("blue");
          break;
        case "dn":
          control = new qx.ui.basic.Label(this.getDn());
          this._add(control, {row: 1, column: 1});
          control.setTextColor("green");
          break;
        case "description":
          control = new qx.ui.basic.Label(this.getDescription());
          this._add(control, {row: 2, column: 1});
          control.setRich(true);
          break;
      }

      // Forward child events to ourselves
      if(control){
        control.setAnonymous(true); 
      }
      return control || this.base(arguments, id);
    },

    _forwardStates :
    {
      focused : true,
      hovered : true,
      selected : true,
      dragover : true
    }
  }
});
