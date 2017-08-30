/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

qx.Class.define("gosa.proxy.Object", {

  extend: qx.core.Object,

  construct: function(data){

    // Call parent contructor
    this.base(arguments);
    this._setAttributes(data);
    this._listeners = new qx.data.Array();
    this._listeners.push(gosa.io.Sse.getInstance().addListener("objectModified", this._objectEvent, this));
    this._listeners.push(gosa.io.Sse.getInstance().addListener("objectRemoved", this._objectEvent, this));
    this._listeners.push(gosa.io.Sse.getInstance().addListener("objectMoved", this._objectEvent, this));
    this._listeners.push(gosa.io.Sse.getInstance().addListener("objectClosing", this._objectClosingEvent, this));

    this.debouncedMergeChanges = qx.util.Function.debounce(this.mergeChanges, 250, false);
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
    },

    /**
     * Title to identify this object, usually the first part of the DN
     */
    $$title: {
      check: "String",
      init: "",
      event: "changedTitle"
    },

    /**
     * Optional Icon to identify this object (used in the upper toolbar that shows the open objects)
     */
    $$icon: {
      check: "String",
      nullable: true
    },

    /**
     * Must be true if the object shall write updates to the backend.
     */
    writeAttributeUpdates : {
      check : "Boolean",
      init : true
    }
  },

  events: {
    "foundDifferencesDuringReload": "qx.event.type.Data",
    "propertyUpdateOnServer": "qx.event.type.Data",
    "updatedAttributeValues": "qx.event.type.Data",
    "moved": "qx.event.type.Data",
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

    setClosed : function(value) {
      qx.core.Assert.assertBoolean(value);
      this._closed = value;
    },

    _objectClosingEvent: function(e) {
      // Skip event processing while committing, removing, etc
      if(this.skipEvents){
        return;
      }
      var data = e.getData();
      // Skip events that are not for us
      if(data.uuid != this.uuid) {
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
      if(data.uuid !== this.uuid){
        return;
      }

      // Act on the event type
      if(data.changeType === "remove") {
        this.fireEvent("removed");
      } else if (data.changeType === "move") {
        this.reload();
        this.fireDataEvent("moved", data.dn);
      } else if(data.changeType === "update"){
        if(!this.is_reloading){

          if(!this.isUiBound()){
            this.reload();
          } else {
            this.debouncedMergeChanges();
          }
        }
      }
    },

    /**
     * Helper method that sets attribute values using the
     * json-rpc response
     */
    _setAttributes: function(data){

      // Initialize object values
      this.initialized = false;
      this.instance_uuid = data.__jsonclass__[1][1];
      this.dn = data.__jsonclass__[1][2];
      this.uuid = data.uuid;

      for(var item in this.attributes){
        var val;
        if(this.attributes[item] in data){

          if(this.attribute_data[this.attributes[item]].multivalue){
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

    /**
     * Setter method for object values
     */
    setAttribute: function(name, value){
      if (this.initialized && this.isWriteAttributeUpdates()) {

        // Do nothing..
        if (value === null || value === undefined) {
          return;
        }

        var rpc = gosa.io.Rpc.getInstance();
        var rpc_value = null;
        if (this.attribute_data[name].multivalue) {
          rpc_value = value.toArray();
        } else {
          if(value.getLength()){
            rpc_value = value.toArray()[0];
          }
        }
        rpc.cA("setObjectProperty", this.instance_uuid, name, rpc_value).bind(this)
        .then(function() {
          this.fireDataEvent("propertyUpdateOnServer", {success: true, error: null, property: name});
        })
        .catch(function(error) {
          this.fireDataEvent("propertyUpdateOnServer", {success: false, error: error, property: name});
        }, this);
      }
    },

    /**
     * Closes the current object
     * @return {qx.Promise}
     */
    close : function(){

      // Skip events now.
      this.skipEvents = true;

      this.setClosed(true);
      this.dispose();
      return gosa.io.Rpc.getInstance().cA("closeObject", this.instance_uuid);
    },

    /**
     * If this object is bound to a gui, then send a merge event to that
     * gui, it will then handle merging.
     */
    mergeChanges: function(){
      return gosa.io.Rpc.getInstance().cA("diffObject", this.instance_uuid)
      .then(qx.lang.Function.curry(this.fireDataEvent, "foundDifferencesDuringReload"), this);
    },

    /**
     *  Reload attribute values from the backend
     * @return {qx.Promise}
     */
    reload: function(){
      if(this.is_reloading){
        return;
      }
      this.is_reloading = true;
      var rpc = gosa.io.Rpc.getInstance();
      return rpc.cA("reloadObject", this.instance_uuid)
      .then(function(data) {
        this._setAttributes(data);
        this.is_reloading = false;
      }, this)
      .catch(gosa.ui.dialogs.Error.show, this);
    },

    /**
     * Updates attribute values by fetching them from the server.
     *
     * @param skipValueUpdate {Boolean}
     * @return {qx.Promise}
     */
    refreshAttributeInformation: function(skipValueUpdate){

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
      return rpc.cA("dispatchObjectMethod", this.instance_uuid, "get_attribute_values")
      .then(function(data) {
        for (var item in data.value) {

          if (data.values[item]) {
            var attr = this.attribute_data;
            if (attr[item]) {
              attr[item].values = data.values[item];
            }
            this.fireDataEvent("updatedAttributeValues", {
              item   : item,
              values : data.values[item]
            });
          }

          // Do not update the property-value
          if (!skipValueUpdate) {
            var value = null;
            if (data.value[item] === null) {
              var attrData = this.attribute_data[item];
              if (attrData.mandatory && attrData.values && attrData.values.length > 0) {
                value = [attrData.values[0]];
                this.setAttribute(item, new qx.data.Array(value));
              }
              else {
                value = [];
              }
            }
            else {
              if (!(this.attribute_data[item].multivalue)) {
                value = [data.value[item]];
              }
              else {
                value = data.value[item];
              }
            }

            // Update modified attributes but skip RPC requests ...
            if (!compare(this.get(item).toArray(), value)) {

              // Skip RPC actions for this set
              this.initialized = false;
              this.set(item, new qx.data.Array(value));
              this.initialized = true;
            }
          }
        }
        return null;
      }, this);
    },

    /**
     * Reloads the current extension status.
     * @return {qx.Promise}
     */
    refreshMetaInformation : function()
    {
      var rpc = gosa.io.Rpc.getInstance();
      return rpc.cA("dispatchObjectMethod", this.instance_uuid, "get_object_info", this.locale)
      .then(function(data) {
        this.baseType = data.base;
        this.extensionTypes = data.extensions;
      }, this);
    },

    /**
     * Wrapper method for object calls
     *
     * @param method {String} name of the method to call
     * @return {qx.Promise}
     */
    callMethod: function(method){

      // Skip events while saving
      if(method === "commit" || method === "remove"){
        this.skipEvents = true;
      }

      var rpc = gosa.io.Rpc.getInstance();
      var args = ["dispatchObjectMethod", this.instance_uuid, method].concat(Array.prototype.slice.call(arguments, 1));
      return rpc.cA.apply(rpc, args)
      .then(function(result) {
        if (method === "remove") {
          this.close();
          this.skipEvents = false;
        }
        return result;
      }, this);
    }
  }
});
