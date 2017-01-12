/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Mixin that allows bidirectional bindings between to properties.
 */
qx.Mixin.define("gosa.data.MBidirectionalBinding", {

  members : {
    __bidirectionalBindings : null,

    /**
     * Adds a bidirectional binding between obj1 and obj2.
     *
     * @param obj1 {qx.core.Object}
     * @param property1 {String}
     * @param obj2 {qx.core.Object}
     * @param property2 {String}
     */
    addBidirectionalBinding : function(obj1, property1, obj2, property2) {
      qx.core.Assert.assertQxObject(obj1);
      qx.core.Assert.assertQxObject(obj2);
      qx.core.Assert.assertString(property1);
      qx.core.Assert.assertString(property2);

      // cannot be initialized in constructor as this method might be used before the mixin constructor is called
      if (this.__bidirectionalBindings === null) {
        this.__bidirectionalBindings = {};
      }

      if (!qx.Class.hasProperty(obj1.constructor, property1)) {
        this.error("Bidirectional binding not possible : the class '" + obj1.constructor.classname + "' does not have a property with the name '" + property1 + "'.");
        return;
      }
      if (!qx.Class.hasProperty(obj2.constructor, property2)) {
        this.error("Bidirectional binding not possible : the class '" + obj2.constructor.classname + "' does not have a property with the name '" + property2+ "'.");
        return;
      }

      var eventName1 = qx.Class.getPropertyDefinition(obj1.constructor, property1).event;
      var eventName2 = qx.Class.getPropertyDefinition(obj2.constructor, property2).event;

      if (!eventName1) {
        this.error("Bidirectional binding not possible: the property '" + property1 + "' of class '" + obj1.constructor.classname + "' has no event.");
        return;
      }
      if (!eventName2) {
        this.error("Bidirectional binding not possible: the property '" + property2 + "' of class '" + obj2.constructor.classname + "' has no event.");
        return;
      }

      var map = this.__bidirectionalBindings;
      var id;
      var ignoreNext = false;

      id = obj1.addListener(eventName1, function(event) {
        if (ignoreNext) {
          ignoreNext = false;
        }
        else {
          ignoreNext = true;
          obj2.set(property2, event.getData());
        }
      });
      map[id] = obj1;

      id = obj2.addListener(eventName1, function(event) {
        if (ignoreNext) {
          ignoreNext = false;
        }
        else {
          ignoreNext = true;
          obj1.set(property1, event.getData());
        }
      });
      map[id] = obj2;
    },

    __removeAllBidirectionalBindings : function() {
      var map = this.__bidirectionalBindings;

      var obj;
      for (var id in map) {
        if (map.hasOwnProperty(id)) {
          obj = map[id];
          if (!obj.isDisposed()) {
            obj.removeListenerById(id);
          }
        }
      }

      this.__bidirectionalBindings = {};
    }
  },

  destruct : function() {
    this.__removeAllBidirectionalBindings();
    this.__bidirectionalBindings = null;
  }
});
