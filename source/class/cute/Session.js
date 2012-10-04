qx.Class.define("cute.Session",
{
  extend: qx.core.Object,

  type: "singleton",

  properties: {
    "loggedInName": {
      init : "",
      check: "String",
      nullable: true,
      event: "_changedLoggedInName"
    },

    /*! \brief  The currently logged in user as JS object.
      *          If nobody is logged in, it is 'null'.
      */
    "user": {
      init : "",
      check: "String",
      nullable: true,
      event: "_changedUser",
      apply: "_changedUser"
    }
  },

  members: {
    _changedUser: function(name){
      if(name !== null){
        var rpc = cute.io.Rpc.getInstance();
        rpc.cA(function(result, error){
            this.setLoggedInName(result['givenName'] + " " + result['sn']);
          }, this, "getUserDetails");
      }else{
        this.setLoggedInName(null);
      }
    },

    logout: function(){
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(result, error){
        this.setUser(null);
        document.location.reload();
      }, this, "logout");
    }
  }
});
