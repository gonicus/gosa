qx.Class.define("cute.proxy.dataTypes.Binary", {
 
  extend : qx.core.Object, 

  construct: function(value){
    this.data = value;
  },

  members: {

    data: null,

    get : function(){
      return(this.data);
    }
  }
});
