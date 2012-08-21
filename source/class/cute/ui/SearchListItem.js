/*
#asset(cute/*)
*/

qx.Class.define("cute.ui.SearchListItem", {

  extend: qx.ui.core.Widget,
  implement : [qx.ui.form.IModel],
  include : [qx.ui.form.MModelProperty],

  construct: function(){
    this.base(arguments);

    this.setMarginBottom(10);
    this.setSelectable(false);

    this._setLayout(new qx.ui.layout.Canvas());

    var container = this._container = new qx.ui.container.Composite();
    var blocker = this._blocker = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
    blocker.add(new qx.ui.basic.Image("cute/reloading.gif"), {top: 22, left: 22});
    blocker.setBackgroundColor("black");
    blocker.setOpacity(0.2);
    blocker.exclude();


    var layout = new qx.ui.layout.Grid();
    layout.setColumnFlex(1, 2);
    layout.setRowFlex(1, 2);
    layout.setSpacing(0);
    container.setLayout(layout);

    // create and add Part 3 to the toolbar
    this._toolbar = new qx.ui.container.Composite(new qx.ui.layout.HBox(0));
    var Button1 = new qx.ui.toolbar.Button(null, cute.Config.getImagePath("actions/document-edit.png", 22));
    var Button2 = new qx.ui.toolbar.Button(null, cute.Config.getImagePath("actions/document-close.png", 22));
    this._toolbar.add(Button1);
    this._toolbar.add(Button2);
    this._toolbar.setAllowGrowY(false);
    this._toolbar.setAllowGrowX(false);
    container.add(this._toolbar, {row: 0, column: 2, rowSpan: 3});

    Button1.addListener("execute", function(){
        this.fireDataEvent("edit", this.getModel());
      }, this);

    this.addListener("mouseover", this._onMouseOver, this);
    this.addListener("mouseout", this._onMouseOut, this);

    this.setAppearance("SearchListItem");
    this._toolbar.hide();
    this._add(container,  {top:0, left:0, right:0, bottom:0});
    this._add(blocker,  {top:0, left:0, right:0, bottom:0});
  },

  destruct : function(){
    this._disposeObjects("_toolbar");
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
    },

    isLoading :
    {
      check : "Boolean",
      nullable : false,
      apply: "_applyIsLoading",
      event : "changeIsLoading",
      init : 0
    }
  },


  members:{

    _toolbar: null,
    _blocker: null,
    _container: null,

    _applyIsLoading: function(value){
      if(value){
        this._blocker.show();
      }else{
        this._blocker.exclude();
      }
    },
    
    _forwardStates: {
      focused : false,
      hovered : false,
      selected : false,
      dragover : false
    },

    _onMouseOver : function() {
      this.addState("hovered");
      this._toolbar.show();
    },

    _onMouseOut : function() {
      this.removeState("hovered");
      this._toolbar.hide();
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
      if(widget && value){
        widget.setSource(cute.Config.getImagePath("objects/" + (value || "null.png"), 64));
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
          control = new qx.ui.basic.Image(cute.Config.getImagePath("objects/" + (this.getIcon() || "null.png"), 64));
          control.setHeight(64);
          control.setScale(true);
          control.setWidth(64);
          control.setAppearance("SearchListItem-Icon");
          control.setAnonymous(true); 
          this._container.add(control, {row: 0, column: 0, rowSpan: 3});
          break;
        case "title":
          control = new qx.ui.basic.Label(this.getTitle());
          this._container.add(control, {row: 0, column: 1});
          control.setAppearance("SearchLIstItem-Title");
          control.addListener("click", function(){
              this.fireDataEvent("edit", this.getModel());
            }, this);
          break;
        case "dn":
          control = new qx.ui.basic.Label(this.getDn());
          this._container.add(control, {row: 1, column: 1});
          control.setAppearance("SearchLIstItem-Dn");
          control.setAnonymous(true); 
          control.setSelectable(true);
          break;
        case "description":
          control = new qx.ui.basic.Label(this.getDescription());
          control.setAnonymous(true); 
          this._container.add(control, {row: 2, column: 1});
          control.setAppearance("SearchLIstItem-Description");
          control.setRich(true);
          control.setSelectable(false);
          break;
      }

      return control || this.base(arguments, id);
    }
  }
});
