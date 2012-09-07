qx.Class.define("cute.proxy.Object", {

  extend: qx.core.Object,

  construct: function(data){

    // Call parent contructor
    this.base(arguments);

    // Initialize object values
    this.initialized = false;
    this.uuid = data["__jsonclass__"][1][1];
    this.dn = data["__jsonclass__"][1][2];

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

  events: {
    "propertyUpdateOnServer": "qx.event.type.Data"
  },

  members: {
    initialized: null,

    /* Setter method for object values
     * */
    setAttribute: function(name, value){
      if(this.initialized){
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
        }, this ,"setObjectProperty", this.uuid, name, rpc_value);
      }
    },

    /* Closes the current object
     * */
    close : function(func, context){
      var rpc = cute.io.Rpc.getInstance();
      var args = ["closeObject", this.uuid];
      rpc.cA.apply(rpc, [function(result, error){
          if(func){
            func.apply(context, [result, error]);
          }
        }, this].concat(args));
    },

    /* Closes the current object
     * */
    refreshMetaInformation : function(cb, ctx)
    {
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(data, context, error){
        if(!error){
          this.baseType = data['base'];
          this.extensionTypes = data['extensions'];
          this.templates = data['templates'];
          cb.apply(ctx);
        }else{
          this.error(error);
        }
      }, this, "dispatchObjectMethod", this.uuid, "get_object_info", this.locale, this.theme);
    },

    /* Wrapper method for object calls
     * */
    callMethod: function(method, func, context){
      var rpc = cute.io.Rpc.getInstance();
      var args = ["dispatchObjectMethod", this.uuid, method].concat(Array.prototype.slice.call(arguments, 3));
      rpc.cA.apply(rpc, [function(result, error){
          if(func){
            func.apply(context, [result, error]);
          }
        }, this].concat(args));
    }
  }
});
