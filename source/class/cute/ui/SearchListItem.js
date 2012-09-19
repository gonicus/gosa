/*
#asset(cute/*)
 */

qx.Class.define("cute.ui.SearchListItem", {

  extend: qx.ui.core.Widget,
  implement : [qx.ui.form.IModel],
  include : [qx.ui.form.MModelProperty],

  /*
   * @lint ignoreUndefined(getThrobber)
   */
  construct: function(){
    this.base(arguments);

    this.setMarginBottom(10);
    this.setSelectable(false);

    this._setLayout(new qx.ui.layout.Canvas());

    var layout = new qx.ui.layout.Grid();
    layout.setColumnFlex(1, 2);
    layout.setRowFlex(1, 2);
    layout.setSpacing(0);
    this._setLayout(layout);

    // create and add Part 3 to the toolbar
    this._toolbar = new qx.ui.container.Composite(new qx.ui.layout.HBox(0));
    var Button1 = new qx.ui.toolbar.Button(null, cute.Config.getImagePath("actions/document-edit.png", 22));
    var Button2 = new qx.ui.toolbar.Button(null, cute.Config.getImagePath("actions/document-close.png", 22));
    this._toolbar.add(Button1);
    this._toolbar.add(Button2);
    this._toolbar.setAllowGrowY(false);
    this._toolbar.setAllowGrowX(false);
    this._add(this._toolbar, {row: 0, column: 2, rowSpan: 3});

    Button1.addListener("execute", function(){
        this.fireDataEvent("edit", this.getModel());
      }, this);

    Button2.addListener("execute", function(){
        this.fireDataEvent("remove", this.getModel());
      }, this);

    // Hide the toolbar as default
    this.setAppearance("SearchListItem");
    this._toolbar.hide();
    this.addListener("mouseover", this._onMouseOver, this);
    this.addListener("mouseout", this._onMouseOut, this);

    // Append the throbber
    var throb = getThrobber({color: "#FFF", alpha: 1});
    this._throbber = throb;
    this.addListener("appear", function(){
        if(this._throbber_pane){
          throb.appendTo(this._throbber_placeholder.getContainerElement().getDomElement());
        }
      }, this);
  },

  destruct : function(){
    this._disposeObjects("_toolbar");
  },

  events: {
    "edit": "qx.event.type.Data",
    "remove": "qx.event.type.Data"
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
      init : false
    }
  },


  members:{

    _toolbar: null,
    _throbber_pane: null,
    _throbber_placeholder: null,

    _applyIsLoading: function(value){
      if(value){
        this._throbber.start();
        this._throbber_pane.setOpacity(0.3);
      }else{
        this._throbber.stop();
        this._throbber_pane.setOpacity(0);
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
      this._toolbar.show();
    },

    _onMouseOut : function() {
      this.removeState("hovered");
      this._toolbar.hide();
    },

    _applyTitle: function(value){

      // Reset the loading state
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
      var control = null;

      switch(id)
      {
        case "icon":

          var icon;
          if (this.getIcon()) {
              if (this.getIcon().indexOf("data:") == 0 || this.getIcon().indexOf(cute.Config.spath) == 0) {
                  icon = this.getIcon();
              } else {
                  icon = cute.Config.getImagePath("objects/" + this.getIcon(), 64);
              }
          } else {
              icon = cute.Config.getImagePath("objects/" + "null.png", 64);
          }
          control = new qx.ui.basic.Image(icon);
          control.setHeight(64);
          control.setScale(true);
          control.setWidth(64);
          control.setMarginRight(5);
          control.setAppearance("SearchListItem-Icon");
          control.setAnonymous(true); 

          /* Create the throbber panes
           * */
          var container = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
          container.add(control, {top: 0, left:0, right:0, bottom:0});
          this._throbber_pane = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
          this._throbber_pane.setBackgroundColor("#000");
          this._throbber_pane.setOpacity(0);
          this._throbber_placeholder = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
          this._throbber_pane.add(this._throbber_placeholder, {left: 16, top: 16});
          container.add(this._throbber_pane, {top: 1, left:1, right: 1, bottom: 1});

          this._add(container, {row: 0, column: 0, rowSpan: 3});
          break;
        case "title":
          control = new qx.ui.basic.Label(this.getTitle());
          this._add(control, {row: 0, column: 1});
          control.setAppearance("SearchLIstItem-Title");
          control.addListener("click", function(){
              this.fireDataEvent("edit", this.getModel());
            }, this);
          control.setRich(true);
          break;
        case "dn":
          control = new qx.ui.basic.Label(this.getDn());
          this._add(control, {row: 1, column: 1});
          control.setAppearance("SearchLIstItem-Dn");
          control.setAnonymous(true); 
          control.setSelectable(true);
          control.setRich(true);
          break;
        case "description":
          control = new qx.ui.basic.Label(this.getDescription());
          control.setAnonymous(true); 
          this._add(control, {row: 2, column: 1});
          control.setAppearance("SearchLIstItem-Description");
          control.setRich(true);
          control.setSelectable(false);
          break;
      }

      return control || this.base(arguments, id);
    }
  }
});
