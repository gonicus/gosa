/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.Session",
{
  extend: qx.core.Object,

  type: "singleton",

  construct: function(){

    this.base(arguments);

    //TODO: go SSE, maybe use Bus
    //gosa.io.WebSocket.getInstance().addListener("objectModified", this._objectEvent, this);
    //gosa.io.WebSocket.getInstance().addListener("objectRemoved", this._objectEvent, this);
  },

  properties: {

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
    "base": {
      init : "",
      check: "String",
      nullable: true,
      event: "_changedBase"
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
      event: "_changedDn"
    },
    "commands" : {
      init : null,
      check : "Array",
      nullable : true
    }
  },

  members: {

    /**
     * Checks if the user has permission to execute the given command.
     *
     * @param command {String}
     * @return {Boolean}
     */
    isCommandAllowed : function(command) {
      qx.core.Assert.assertString(command);
      qx.core.Assert.assertArray(this.getCommands());

      var splitted = command.split("(");
      if (splitted.length > 0) {
        command = splitted[0];
      }
      return qx.lang.Array.contains(this.getCommands(), command);
    },

    _objectEvent: function(e){

      // Skip events that are not for us
      var data = e.getData();
      if(data['uuid'] != this.getUuid()){
        return;
      }

      // Act on the event type
      if(data['changeType'] == "remove"){
        this.logout();
      }else if(data['changeType'] == "update"){
        this._changedUser(this.getUser());
      }
    },

    _changedUser: function(name){
      if(name !== null){
        var rpc = gosa.io.Rpc.getInstance();
        rpc.cA("getUserDetails")
        .then(function(result) {
          this.setSn(result['sn']);
          this.setCn(result['cn']);
          this.setGivenName(result['givenName']);
          this.setDn(result['dn']);
          this.setUuid(result['uuid']);
        }, this)
        .catch(function(error) {
          // var d = new gosa.ui.dialogs.Error(new qx.ui.core.Widget().tr("Failed to fetch current user information."));
          var d = new gosa.ui.dialogs.Error(error.message);
          d.open();
          d.addListener("close", function(){
            gosa.Session.getInstance().logout();
          }, this);
        });
      }else{
        this.setSn(null);
        this.setCn(null);
        this.setGivenName(null);
        this.setDn(null);
        this.setUuid(null);
      }
    },

    logout: function(){
      var rpc = gosa.io.Rpc.getInstance();
      rpc.cA("logout").then(function() {
        this.setUser(null);
        document.location.reload();
      }, this);
    }
  }
});
