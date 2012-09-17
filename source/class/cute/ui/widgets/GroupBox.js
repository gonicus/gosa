qx.Class.define("cute.ui.widgets.GroupBox", {

  extend: qx.ui.groupbox.GroupBox,

  construct: function(title){
    this.base(arguments, title);

    this.__add = this.add;
    this.__cuteChildList = [];

    this.addListenerOnce("appear", function(){
        this.__cuteChildList = this.loadChildrenList(this.getChildren());
      }, this);
    
  },

  members: {

    __cuteChildList: null,
    
    __check: function(){
      var disable = true;
      for(var i=0; i<this.__cuteChildList.length; i++){
        if(this.__cuteChildList[i].getVisibility() == "visible"){
          disable = false;
          break;
        }
      }
      if(disable){
        this.exclude();
      }else{
        this.show();
      }
    },

    loadChildrenList: function(current){
      var children = [];
      for(var i=0; i< current.length; i++){

        if(current[i].hasState && current[i].hasState("cuteInput")){
          children.push(current[i]); 
          current[i].addListener("changeVisibility", this.__check, this);      
        }

        if(current[i].getChildren){
          children = children.concat(this.loadChildrenList(current[i].getChildren()));
        }
      }
      return(children);
    }
  }
});
