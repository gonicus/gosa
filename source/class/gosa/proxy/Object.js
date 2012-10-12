qx.Class.define("gosa.proxy.Object", {

  extend: qx.core.Object,

  construct: function(data){

    // Call parent contructor
    this.base(arguments);
    this._setAttributes(data);
    this._listenerID1 = gosa.io.WebSocket.getInstance().addListener("objectModified", this._objectEvent, this);
    this._listenerID2 = gosa.io.WebSocket.getInstance().addListener("objectRemoved", this._objectEvent, this);
  },

  destruct : function(){

    // Stop listening for object changes
    gosa.io.WebSocket.getInstance().removeListenerById(this._listenerID1);
    gosa.io.WebSocket.getInstance().removeListenerById(this._listenerID2);

    // Remove every listener that was attached to us.
    // This allows us to set attribute values to null without
    // notifying gui widgets or other things.
    qx.event.Registration.removeAllListeners(this); 
    for(var item in this.attributes){
      this.set(this.attributes[item], null);
    }
  },

  events: {
    "propertyUpdateOnServer": "qx.event.type.Data",
    "removed": "qx.event.type.Event",
    "reloaded": "qx.event.type.Event"
  },

  members: {

    _closed: false,
    _listenerID1: null,
    _listenerID2: null,
    initialized: null,
    is_reloading: false,
    _updateLastChanged: null,
    skipEvents: false,

    isClosed: function(){
      return(this.isDisposed() || this._closed);
    },

    _objectEvent: function(e){

      // Skip event processing while commiting, removing, etc
      if(this.skipEvents){
        return;
      }

      // Skip events that are not for us
      var data = e.getData();
      if(data['uuid'] != this.uuid){
        return;
      }

      // Act on the event type
      if(data['changeType'] == "remove"){
        this.fireEvent("removed");
      }else if(data['changeType'] == "update"){
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
        var rpc = gosa.io.Rpc.getInstance();
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

      // Skip events now.
      this.skipEvents = true;

      this.isClosed = true;
      this.dispose();
      var rpc = gosa.io.Rpc.getInstance();
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
      this.is_reloading = true;
      var rpc = gosa.io.Rpc.getInstance();
      rpc.cA(function(data, error){
          this._setAttributes(data);
          this.is_reloading = false;
          this.fireEvent("reloaded");
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

      var rpc = gosa.io.Rpc.getInstance();
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
      var rpc = gosa.io.Rpc.getInstance();
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

      // Skip events while saving
      if(method == "commit" || method == "remove"){
        this.skipEvents = true;
      }

      var rpc = gosa.io.Rpc.getInstance();
      var args = ["dispatchObjectMethod", this.instance_uuid, method].concat(Array.prototype.slice.call(arguments, 3));
      rpc.cA.apply(rpc, [function(result, error){
          if(func){
            func.apply(context, [result, error]);
            if(method in ["remove"]){
              this.close();
              this.skipEvents = false;
            }
          }
        }, this].concat(args));
    }
  }
});
