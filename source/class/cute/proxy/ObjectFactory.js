qx.Class.define("cute.proxy.ObjectFactory", {

  extend: qx.core.Object,

  construct: function(){
    this.base(arguments);

    if(!cute.proxy.ObjectFactory.classes){
      cute.proxy.ObjectFactory.classes = {}
    }
  },

  statics: {
    classes: null,

    openObject: function(c_callback, c_context, dn, type){

      // Initialize class-cache
      if(!cute.proxy.ObjectFactory.classes){
        cute.proxy.ObjectFactory.classes = {};
      }

      // Add an event listener
      var rpc = cute.io.Rpc.getInstance();
      rpc.cA(function(userData, context, error){

        // Extract required user information out of the '__jsonclass__' result object.
        var jDefs = userData["__jsonclass__"][1];
        var uuid = jDefs[1];
        var methods = jDefs[3];
        var attributes = jDefs[4];
        var baseType = null;
        var extensionTypes = null;
        var templates = {};
        var translations = {};
        var attribute_data = {};

        // This method is called below to make the code more readable.
        var _handleResult = function(){

          // This is the new classname for the metaclass.
          // e.g. objects.User
          var className = "objects." + baseType;

          // Create a metaclass for this type of objects on demand, if not done already.
          if(className in cute.proxy.ObjectFactory.classes){
            c_callback.apply(c_context, [new cute.proxy.ObjectFactory.classes[className](userData)]); 
          }else{

            // The base member variables for the metaclass
            var members = {
                uuid: null,
                methods: methods,
                attributes: attributes,
                attribute_data: attribute_data,
                baseType: baseType,
                templates: templates,
                translations: translations,
                extensionTypes: extensionTypes
              };

            // this closure returns a new apply method for the given attribute.
            var getApplyMethod = function(name){
              var func = function(value){
                this.setAttribute(name, value);
              };
              return(func);
            }

            // this closure returns a new wrapper-method for an object method
            var getMethod = function(name){
              var func = function(){
                return(this.callMethod.apply(this, [name].concat(Array.prototype.slice.call(arguments))));
              };
              return(func);
            }

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
            var def = {extend: cute.proxy.Object, members: members, properties: properties};
            cute.proxy.ObjectFactory.classes[className] = qx.Class.define(className, def);
            c_callback.apply(c_context, [new cute.proxy.ObjectFactory.classes[className](userData)]); 
          }
        }

        var theme = "default";
        if (cute.Config.theme) {
            theme = cute.Config.theme;
        }

        var locale;
        if (cute.Config.locale) {
            locale = cute.Config.locale;
        } else {
          locale = qx.bom.client.Locale.getLocale();
          var variant = qx.bom.client.Locale.getVariant();
          if (locale && variant) {
              locale = locale + "-" + variant;
          }
        }

	      // Load object info - base type, extension types and template information
        rpc.cA(function(data, context, error){
            if(!error){
              baseType = data['base'];
              extensionTypes = data['extensions'];
              templates = data['templates'];
              translations = data['i18n'];

              rpc.cA(function(_attribute_data, error) {

                if(!error){
                  // Call the result handling method, we had defined earlier above.
                  attribute_data = _attribute_data;
                  _handleResult(userData);
                }
              }, this, "dispatchObjectMethod", uuid, "get_attributes", true);

            }else{
              this.error(error);
            }
        }, this, "dispatchObjectMethod", uuid, "get_object_info", locale, theme);

      }, this, "openObject", "object", dn, type);
    }
  }
});
