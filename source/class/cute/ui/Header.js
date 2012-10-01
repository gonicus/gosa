qx.Class.define("cute.ui.Header", {

  extend: qx.ui.container.Composite,

  construct: function(){

    this.base(arguments);

    this.setLayout(new qx.ui.layout.Canvas());


    var header = new qx.ui.basic.Atom("", "cute/logo.png");
    header.setBackgroundColor("black");
    header.setTextColor("white");
    header.setHeight(48);
    header.setPadding(5);
    header.setFont(qx.bom.Font.fromString("sans-serif 28"));
    this.add(header, {top:0, left:0, bottom: 0, right: 0});

    this.__label = new qx.ui.basic.Label("");
    this.__label.setTextColor("white");
    this.add(this.__label, {top:10, right: 10});

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
