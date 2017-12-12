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

qx.Class.define("gosa.proxy.ObjectFactory", {

  extend: qx.core.Object,

  construct: function(){
    this.base(arguments);

    if(!gosa.proxy.ObjectFactory.classes){
      gosa.proxy.ObjectFactory.classes = {};
    }
  },

  statics: {
    classes: null,

    /**
     * Wrapper for {this.__openObject} to open a workflow object
     *
     * @param workflowId {String} id of the workflow
     * @param reference_object_dn {String} dn of a reference object that should be used to prefill the workflow object
     * @return {qx.Promise}
     */
    openWorkflow: function(workflowId, reference_object_dn){
      return this.__openObject("workflow", workflowId, reference_object_dn);
    },

    /**
     * Wrapper for {this.__openObject} to open a object
     *
     * @param dn {String} DN of the object
     * @param type {String} type of the object
     * @return {qx.Promise}
     */
    openObject: function(dn, type){
      return this.__openObject("object", dn, type);
    },

    openObjectByType: function(key, value, type) {
      // Initialize class-cache
      if(!gosa.proxy.ObjectFactory.classes){
        gosa.proxy.ObjectFactory.classes = {};
      }
      return gosa.io.Rpc.getInstance().cA("openObjectByType", key, value, type).then(function(userData) {
        return this.__createObject("object", userData);
      }, this);
    },

    __openObject: function(object_type, dn, type){

      // Initialize class-cache
      if(!gosa.proxy.ObjectFactory.classes){
        gosa.proxy.ObjectFactory.classes = {};
      }

      // Add an event listener
      return gosa.io.Rpc.getInstance().cA("openObject", object_type, dn, type).then(function(userData) {
        return this.__createObject(object_type, userData);
      }, this);
    },

    __createObject: function(object_type, userData) {
      var rpc = gosa.io.Rpc.getInstance();
      var jDefs = userData["__jsonclass__"][1];
      var uuid = jDefs[1];
      var locale = gosa.Config.getLocale();
      var promises = [];
      if (object_type === "object") {
        // Load object info - base type, extension types
        promises = [
          userData,
          rpc.cA("dispatchObjectMethod", uuid, "get_attributes", true),
          rpc.cA("dispatchObjectMethod", uuid, "get_object_info", locale)
        ];
      } else if (object_type === "workflow") {
        promises = [
          userData,
          rpc.cA("dispatchObjectMethod", uuid, "get_attributes", true)
        ];
      }
      return qx.Promise.all(promises)
      .spread(function(userData, _attribute_data, info) {

        // Extract required user information out of the '__jsonclass__' result object.
        var jDefs = userData["__jsonclass__"][1];
        var uuid = jDefs[1];
        var methods = jDefs[4];
        var attributes = jDefs[5];

        var locale = gosa.Config.getLocale();
        if (object_type === "object") {
          var className = gosa.proxy.ObjectFactory.createClass(object_type, info, methods, attributes, _attribute_data, locale);
          return new gosa.proxy.ObjectFactory.classes[className](userData);
        } else if (object_type === "workflow") {
          var data = {
            className : "workflows."+uuid,
            id : uuid,
            base : "Workflow."+uuid,
            extensions: null,
            extensionDeps: null
          };
          var className = gosa.proxy.ObjectFactory.createClass(object_type, data, methods, attributes, _attribute_data, locale);
          return new gosa.proxy.ObjectFactory.classes[className](userData);
        }
      });
    },

    createClass: function(object_type, data, methods, attributes, attribute_data, locale) {
      // This is the new classname for the metaclass.
      // e.g. objects.User or workflows.create_user
      var className = data['className'] ? data['className'] : object_type+"s."+data['base'];

      var members = {
        instance_uuid: null,
        dn: null,
        methods: methods,
        attributes: attributes,
        attribute_data: attribute_data,
        baseType: data['base'],
        extensionTypes: data['extensions'],
        extensionDeps: data['extension_deps'],
        extensionStates: data['extension_states'],
        locale: locale
      };
      if (data['id']) {
        members['id'] = data['id'];
      }

      // this closure returns a new apply method for the given attribute.
      var getApplyMethod = function(name){
        var func = function(value){
          this.setAttribute(name, value);
        };
        return(func);
      };

      // this closure returns a new wrapper-method for an object method
      var getMethod = function(name){
        var func = function(){
          return(this.callMethod.apply(this, [name].concat(Array.prototype.slice.call(arguments))));
        };
        return(func);
      };

      // Create list of properties
      var properties = {};
      for(var attr in attributes){
        var name = attributes[attr];
        var upperName = qx.lang.String.firstUp(name);
        var applyName = "_apply_" + upperName;
        var prop = {apply: applyName, event: "changed" + upperName, nullable: true, check: "qx.data.Array"};
        members[applyName] = getApplyMethod(name);
        properties[name] = prop;
      }

      // Create methods
      for(attr in methods){
        var name = methods[attr];
        members[name] = getMethod(name);
      }

      // Create meta class for this object
      var def = {extend: gosa.proxy.Object, members: members, properties: properties};
      gosa.proxy.ObjectFactory.classes[className] = qx.Class.define(className, def);
      return className;
    },

    /**
     * Removes the object given by its uuid
    */
    removeObject: function(uuid) {
      return gosa.io.Rpc.getInstance().cA("removeObject", "object", uuid)
      .catch(function(error) {
        new gosa.ui.dialogs.Error(qx.locale.Manager.tr("Cannot remove entry!")).open();
        this.error("cannot remove entry: " + error);
      }, this);
    }
  }
});
