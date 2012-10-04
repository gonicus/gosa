qx.Class.define("cute.ui.Header", {

  extend: qx.ui.container.Composite,

  construct: function(){

    this.base(arguments);

    this.setLayout(new qx.ui.layout.Canvas());


    var header = new qx.ui.basic.Atom("", "cute/logo.png");
    header.setBackgroundColor("header-bar");
    header.setTextColor("header-text");
    header.setHeight(48);
    header.setPadding(5);
    this.add(header, {top:0, left:0, bottom: 0, right: 0});

    container = new qx.ui.container.Composite(new qx.ui.layout.HBox());
    this.__label = new qx.ui.basic.Label("");
    this.__label.setAlignY("middle");
    this.__label.setTextColor("header-text");
    container.add(this.__label);
    this.add(container, {top:0, bottom:0, right: 10});

    this.__label.addListener("click", function(){
        cute.Session.getInstance().logout();
      }, this);
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
        this.__label.setValue(this.tr("Logged in: %1", value));
      }
    }
  }
});
