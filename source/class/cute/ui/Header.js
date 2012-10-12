qx.Class.define("cute.ui.Header", {

  extend: qx.ui.container.Composite,

  construct: function(){

    this.base(arguments);

    this.setLayout(new qx.ui.layout.Canvas());


    var header = new qx.ui.basic.Atom("", "cute/themes/default/logo.png");
    header.setDecorator("title-bar");
    header.setTextColor("header-text");
    header.setHeight(48);
    header.setPadding(5);
    this.add(header, {top:0, left:0, bottom: 0, right: 0});

    var container = new qx.ui.container.Composite(new qx.ui.layout.HBox(10));
    this.__label = new qx.ui.basic.Label("");
    this.__label.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Edit your profile")));
    this.__label.setRich(true);
    this.__label.setCursor("pointer");
    this.__label.setAlignY("middle");
    this.__label.setTextColor("header-text");
    container.add(this.__label);

    this.__label.addListener("click", function(){
        document.location.href = cute.Tools.createActionUrl('openObject', cute.Session.getInstance().getUuid());
      }, this);

    var btn = new qx.ui.basic.Image("cute/themes/default/btn-logout.png");
    btn.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Logout")));
    btn.setCursor("pointer");
    btn.setAlignY("middle");
    btn.addListener("click", function(){
        cute.Session.getInstance().logout();
      }, this);
    container.add(btn);

    this.add(container, {top:0, bottom:0, right: 10});
  }, 

  properties: {
  
    loggedInName: {
      init: "",
      check: "String",
      event: "_changedLoggedInName",
      nullable: true,
      apply: "setLoggedInName"
    }
  },

  members: {

    __label: null,

    setLoggedInName: function(value){
      if(value === null){
        this.__label.setValue("");
      }else{
        this.__label.setValue("<b>" + this.tr("Logged in:") + "</b> " + value);
      }
    }
  }
});
