qx.Class.define("cute.ui.widgets.MultiEditContainer", {

  extend: qx.ui.container.Composite,

  properties: {
    widget: {
      init: null,
      apply: "__applyWidget"
    },
    hasAdd: {
      check: "Boolean",
      init: false,
      apply: "__applyHasAdd"
    },
    hasDelete: {
      check: "Boolean",
      init: false,
      apply: "__applyHasDelete"
    }
  },

  construct: function(widget){
    this.base(arguments);

    this.setLayout(new qx.ui.layout.HBox(0));
  
    this.__container = new qx.ui.container.Composite(new qx.ui.layout.HBox(0));
    this.__addButton = new qx.ui.form.Button(null, cute.Config.getImagePath("actions/attribute-add.png", "22")).set({
            "padding": 2,
            "margin": 0
            });
    this.__addButton.setAppearance("attribute-button");
    this.__addButton.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Add value")));
    this.__delButton = new qx.ui.form.Button(null, cute.Config.getImagePath("actions/attribute-remove.png", "22")).set({
            "padding": 2,
            "margin": 0
            });
    this.__delButton.setAppearance("attribute-button");
    this.__delButton.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Remove value")));

    this.add(this.__container, {flex: 1});
    this.add(this.__addButton);
    this.add(this.__delButton);

    this.__addButton.addListener("execute", function(){
        this.fireEvent("add");
      }, this);

    this.__delButton.addListener("execute", function(){
        this.fireEvent("delete");
      }, this);

    if(widget){
      this.setWidget(widget);
    }
  },

  destruct : function(){
    this._disposeObjects("__container", "__addButton", "__delButton");
  },

  events: {
    "add": "qx.event.type.Event",
    "delete": "qx.event.type.Event"
  },

  members: {
    __addButton: null,
    __delButton: null,
    __container: null,

    __applyWidget: function(w){
      this.__container.removeAll();
      if(w){
        this.__container.add(w, {flex:1});
      }
    },

    __applyHasAdd: function(value){
      if(value){
        this.__addButton.show();
      }else{
        this.__addButton.exclude();
      }
    },

    __applyHasDelete: function(value){
      if(value){
        this.__delButton.show();
      }else{
        this.__delButton.exclude();
      }
    }
  }
});
