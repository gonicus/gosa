/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.proxy.Object", {

  extend: qx.core.Object,

  construct: function(data){

    // Call parent contructor
    this.base(arguments);
    this._setAttributes(data);
    this._listeners = new qx.data.Array();
    this._listeners.push(gosa.io.Sse.getInstance().addListener("objectModified", this._objectEvent, this));
    this._listeners.push(gosa.io.Sse.getInstance().addListener("objectRemoved", this._objectEvent, this));
    this._listeners.push(gosa.io.Sse.getInstance().addListener("objectClosing", this._objectClosingEvent, this));
  },

  destruct : function(){

    // Stop listening for object changes
    this._listeners.forEach(function(listener) {
      gosa.io.Sse.getInstance().removeListenerById(listener);
    }, this);
    this.__listeners = null;

    // Remove every listener that was attached to us.
    // This allows us to set attribute values to null without
    // notifying gui widgets or other things.
    qx.event.Registration.removeAllListeners(this);
    for(var item in this.attributes){
      this.set(this.attributes[item], null);
    }
  },

  properties: {

    // Bound to the gui-editing widget
    uiBound: {
      check: "Boolean",
      init: false
    }
  },

  events: {
    "foundDifferencesDuringReload": "qx.event.type.Data",
    "propertyUpdateOnServer": "qx.event.type.Data",
    "updatedAttributeValues": "qx.event.type.Data",
    "removed": "qx.event.type.Event",
    "closing": "qx.event.type.Data"
  },

  members: {

    _closed: false,
    _listeners: null,
    initialized: null,
    is_reloading: false,
    _updateLastChanged: null,
    skipEvents: false,

    isClosed: function(){
      return(this.isDisposed() || this._closed);
    },

    _objectClosingEvent: function(e) {
      // Skip event processing while committing, removing, etc
      if(this.skipEvents){
        return;
      }
      var data = e.getData();
      // Skip events that are not for us
      if(data['uuid'] != this.uuid) {
        return;
      }
      this.fireDataEvent("closing", data);
    },

    _objectEvent: function(e){

      // Skip event processing while committing, removing, etc
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

          if(!this.isUiBound()){
            this.reload(function(result, error){
              if(error){
                new gosa.ui.dialogs.Error(error.message).open();
              }
            }, this);
          }else{
            this.mergeChanges();
          }
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
          that.fireDataEvent("propertyUpdateOnServer", {success: !error, error: error, property: name});
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

    /* If this object is bound to a gui, then send a merge event to that
      * gui, it will then handle merging.
      * */
    mergeChanges: function(){
      var rpc = gosa.io.Rpc.getInstance();
      rpc.cA(function(data, error){
          this.fireDataEvent("foundDifferencesDuringReload", data);
        }, this, "diffObject", this.instance_uuid);
    },

    /* Reload attribute values from the backend
     * */
    reload: function(cb, ctx){
      if(this.is_reloading){
        return;
      }
      this.is_reloading = true;
      var rpc = gosa.io.Rpc.getInstance();
      rpc.cA(function(data, error){
        if(!error){
          this._setAttributes(data);
          this.is_reloading = false;
        }
        cb.apply(ctx, [data, error]);
      }, this, "reloadObject", this.instance_uuid);
    },

    /* Updates attribute values by fetching them from the server.
     * */
    refreshAttributeInformation: function(cb, ctx, skipValueUpdate){

      if(!skipValueUpdate){
        skipValueUpdate = false;
      }

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
          for(var item in data['value']){

            // Tell anybody thats interested, that the 'values'-list for the given
            // attribute has changed.
            if(data['values'][item]){
              this.fireDataEvent("updatedAttributeValues", {item: item, values: data['values'][item]});
            }

            // Do not update the property-value
            if(!skipValueUpdate){
              var value = null;
              if(data['value'][item] === null){
                value = [];
              }else{
                if(!(this.attribute_data[item]['multivalue'])){
                  value = [data['value'][item]];
                }else{
                  value = data['value'][item];
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
          }
          if(cb){
            cb.apply(ctx);
          }
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
