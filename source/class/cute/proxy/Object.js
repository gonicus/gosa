qx.Class.define("cute.proxy.Object", {

  extend: qx.core.Object,

  construct: function(data){

    // Call parent contructor
    this.base(arguments);
    this._setAttributes(data);
    this._listenerID = cute.io.WebSocket.getInstance().addListener("objectModified", this._objectEvent, this);
  },

  destruct : function(){

    // Stop listening for object changes
    cute.io.WebSocket.getInstance().removeListenerById(this._listenerID);

    // Remove every listener that was attached to us.
    // This allows us to set attribute values to null without
    // notifying gui widgets or other things.
    qx.event.Registration.removeAllListeners(this); 
    for(var item in this.attributes){
      this.set(this.attributes[item], null);
    }
  },

  events: {
    "propertyUpdateOnServer": "qx.event.type.Data"
  },

  members: {

    _listenerID: null,
    initialized: null,
    is_reloading: false,
    _updateLastChanged: null,

    _objectEvent: function(e){

      // Skip events that are not for us
      var data = e.getData();
      if(data['uuid'] != this.uuid){
        return;
      }

      // Act on the event type
      if(data['changeType'] == "remove"){
        //..

      }else if(data['changeType'] == "modify"){
        if(!this.is_reloading){
          this.reload(function(result, error){}, this);
        }
      }
    },

    /* Helper method that sets attribute values using the 
     * json-rpc response
     * */
    _setAttributes: function(data){
    
      // Initialize object values
      this.initialized = false;
      this.instance_uuid = data["__jsonclass__"][1][1];
      this.dn = data["__jsonclass__"][1][2];
      this.uuid = data['uuid'];

      for(var item in this.attributes){
        var val;
        if(this.attributes[item] in data){

          if(this.attribute_data[this.attributes[item]]['multivalue']){
            val = new qx.data.Array(data[this.attributes[item]]);
          }else{
            var value = data[this.attributes[item]];
            val = new qx.data.Array();
            if(value !== null){
              val.push(value);
            }
          }

          this.set(this.attributes[item], val);
        }
      }

      // Initialization is done (Start sending attribute modifications to the backend)
      this.initialized = true;
    },

    /* Setter method for object values
     * */
    setAttribute: function(name, value){
      if(this.initialized){

        // Do nothing..
        if(value == null){
          return
        }

        var that = this;
        var rpc = cute.io.Rpc.getInstance();
        var rpc_value = null;
        if(this.attribute_data[name]['multivalue']){
          rpc_value = value.toArray();
        }else{
          if(value.getLength()){
            rpc_value = value.toArray()[0];
          }
        }

        rpc.cA(function(result, error) {
          this.fireDataEvent("propertyUpdateOnServer", {success: !error, error: error, property: name});
          if(!error){
            that.debug("update property value " + name + ": "+ rpc_value);
          }else{
            that.error("failed to update property value for " + name + "(" + error.message + ")");
          }
        }, this ,"setObjectProperty", this.instance_uuid, name, rpc_value);
      }
    },

    /* Closes the current object
     * */
    close : function(func, context){
      this.dispose();
      var rpc = cute.io.Rpc.getInstance();
      var args = ["closeObject", this.instance_uuid];
      rpc.cA.apply(rpc, [function(result, error){
          if(func){
            func.apply(context, [result, error]);
          }
        }, this].concat(args));
    },

    /* Reload the current object
     * */
    reload: function(cb, ctx){
      if(this.is_reloading){
        return;
      }
      this.error("RELOAD", this.dn);
      this.is_reloading = true;
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(data, error){
          this._setAttributes(data);
          this.is_reloading = false;
          cb.apply(ctx, [data, error]);
        }, this, "reloadObject", this.instance_uuid);
    },

    /* Updates attribute values by fetching them from the server.
     * */
    refreshAttributeValues: function(cb, ctx){

      var compare = function(a, b){
          if(a.length != b.length){
            return(false);
          }
          for(var i=0; i<a.length; i++){
            if(a[i] != b[i]){
              return(false);
            }
          }
          return(true);
        };

      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(data, context, error){
        if(!error){
          for(var item in data){

            var value = null;
            if(data[item] === null){
              value = [];
            }else{
              if(!(this.attribute_data[item]['multivalue'])){
                value = [data[item]];
              }else{
                value = data[item];
              }
            }

            // Update modified attributes but skip RPC requests ...
            if(!compare(this.get(item).toArray(), value)){

              // Skip RPC actions for this set
              this.initialized = false;
              this.set(item, new qx.data.Array(value));
              this.initialized = true;
            }
          }
          cb.apply(ctx);
        }else{
          this.error(error);
        }
      }, this, "dispatchObjectMethod", this.instance_uuid, "get_attribute_values");
    },

    /* Reloads the current extension status.
     * */
    refreshMetaInformation : function(cb, ctx)
    {
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(data, context, error){
        if(!error){
          this.baseType = data['base'];
          this.extensionTypes = data['extensions'];
          cb.apply(ctx);
        }else{
          this.error(error);
        }
      }, this, "dispatchObjectMethod", this.instance_uuid, "get_object_info", this.locale, this.theme);
    },

    /* Wrapper method for object calls
     * */
    callMethod: function(method, func, context){
      var rpc = cute.io.Rpc.getInstance();
      var args = ["dispatchObjectMethod", this.instance_uuid, method].concat(Array.prototype.slice.call(arguments, 3));
      rpc.cA.apply(rpc, [function(result, error){
          if(func){
            func.apply(context, [result, error]);
            if(method in ["remove"]){
              this.close();
            }
          }
        }, this].concat(args));
    }
  }
});
