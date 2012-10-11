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
    },

    "uuid": {
      init : "",
      check: "String",
      nullable: true,
      event: "_changedUUID"
    },
    "sn": {
      init : "",
      check: "String",
      nullable: true,
      event: "_changedSn"
    },
    "givenName": {
      init : "",
      check: "String",
      nullable: true,
      event: "_changedGivenName"
    },
    "cn": {
      init : "",
      check: "String",
      nullable: true,
      event: "_changedCn"
    },
    "dn": {
      init : "",
      check: "String",
      nullable: true,
      event: "_changedCn"
    }
  },

  members: {
    _changedUser: function(name){
      if(name !== null){
        var rpc = cute.io.Rpc.getInstance();
        rpc.cA(function(result, error){
            cute.proxy.ObjectFactory.openObject(function(result, error){
                try{
                  this._object = result;
                  this._object.bind("sn[0]", this, "sn");
                  this._object.bind("cn[0]", this, "cn");
                  this._object.bind("givenName[0]", this, "givenName");
                  this._object.bind("cn[0]", this, "loggedInName");
                  this._object.uuid = result['uuid'];
                  this.setDn(result['dn']);
                  this.setUuid(result['uuid']);
                }catch(e){
                  this.error(e);
                }

              }, this, result['dn']);
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
