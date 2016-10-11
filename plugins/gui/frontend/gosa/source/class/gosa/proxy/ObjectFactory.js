/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

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
     * @param c_callback {Function} callback to call when workflow has been opened
     * @param c_context {Object} context for callback
     * @param workflowId {String} id of the workflow
     */
    openWorkflow: function(c_callback, c_context, workflowId){
      this.__openObject("workflow", c_callback, c_context, workflowId);
    },

    /**
     * Wrapper for {this.__openObject} to open a object
     *
     * @param c_callback {Function} callback to call when object has been opened
     * @param c_context {Object} context for callback
     * @param dn {String} DN of the object
     * @param type {String} type of the object
     */
    openObject: function(c_callback, c_context, dn, type){
      this.__openObject("object", c_callback, c_context, dn, type);
    },

    __openObject: function(object_type, c_callback, c_context, dn, type){

      // Initialize class-cache
      if(!gosa.proxy.ObjectFactory.classes){
        gosa.proxy.ObjectFactory.classes = {};
      }

      // Add an event listener
      var rpc = gosa.io.Rpc.getInstance();
      rpc.cA(function(userData, error){

        // Abort on errors
        if(error){
          c_callback.apply(c_context, [null, error]);
        }else{

          // Extract required user information out of the '__jsonclass__' result object.
          var jDefs = userData["__jsonclass__"][1];
          var uuid = jDefs[1];
          var methods = jDefs[4];
          var attributes = jDefs[5];
          var baseType = null;
          var extensionTypes = null;
          var extensionDeps = null;
          var attribute_data = {};

          var locale = gosa.Config.getLocale();

          // This method is called below to make the code more readable.
          var _handleResult = function(){

            // This is the new classname for the metaclass.
            // e.g. objects.User or workflows.create_user
            var className = object_type + "s." + baseType;

            // The base member variables for the metaclass
            var members = {
              instance_uuid: null,
              dn: null,
              methods: methods,
              attributes: attributes,
              attribute_data: attribute_data,
              baseType: baseType,
              extensionTypes: extensionTypes,
              extensionDeps: extensionDeps,
              locale: locale
            };

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
              var upperName = name.charAt(0).toUpperCase() + name.slice(1);
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
            c_callback.apply(c_context, [new gosa.proxy.ObjectFactory.classes[className](userData)]);
          };

          if (object_type === "object") {
            // Load object info - base type, extension types
            rpc.cA(function(data, error) {
              if (error) {
                c_callback.apply(c_context, [null, error]);
              }
              else {
                baseType = data['base'];
                extensionTypes = data['extensions'];
                extensionDeps = data['extension_deps'];

                rpc.cA(function(_attribute_data, error) {
                  if (error) {
                    c_callback.apply(c_context, [null, error]);
                  }
                  else {
                    // Call the result handling method, we had defined earlier above.
                    attribute_data = _attribute_data;
                    _handleResult(userData);
                  }
                }, this, "dispatchObjectMethod", uuid, "get_attributes", true);

              }
            }, this, "dispatchObjectMethod", uuid, "get_object_info", locale);
          } else if (object_type === "workflow") {

            rpc.cA(function(_attribute_data, error) {
              if (error) {
                c_callback.apply(c_context, [null, error]);
              }
              else {
                // Call the result handling method, we had defined earlier above.
                var className = this.__createWorkflowClass(uuid, methods, attributes, _attribute_data, locale);
                c_callback.apply(c_context, [new gosa.proxy.ObjectFactory.classes[className](userData)]);
              }
            }, this, "dispatchObjectMethod", uuid, "get_attributes", true);
          }
        }
      }, this, "openObject", object_type, dn, type);
    },

    __createWorkflowClass : function(id, methods, attributes, attribute_data, locale) {
      // This is the new classname for the metaclass.
      // e.g. workflows.create_user
      var className = "workflows." + id;

      // The base member variables for the metaclass
      var members = {
        instance_uuid: null,
        dn: null,
        id: id,
        methods: methods,
        attributes: attributes,
        attribute_data: attribute_data,
        baseType: "Workflow."+id,
        locale: locale
      };

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
        var upperName = name.charAt(0).toUpperCase() + name.slice(1);
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
    }
  }
});
