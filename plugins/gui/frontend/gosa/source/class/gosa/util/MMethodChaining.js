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

//noinspection JSUnusedGlobalSymbols
/**
 * This Mixin allows method hooks which can be called before or after a method.
 * This is a possible way circumvent the problem that mixin cannot override methods of
 * the including classes, instead one can add an "after" hook for the method.
 * The downside is that the main class method has to be augmented with calls to the hook processor.
 *
 *  <h3>Example</h3>
 *  Adding child controls by Mixins:
 *  To add child controls by Mixins you have to add an 'after' hook to the '_createChildControlImpl' method.
 *  E.g. if the Mixin's child control generating method is called '__createMixinChildControlImpl' you can add the hook like this:
 *  <pre class="javascript">
 *    this.addHook("after", "_createChildControlImpl", this.__createMixinChildControlImpl, this);
 *  </pre>
 *  Having done that you have to add the processor call to the main classes '_createChildControlImpl'-method like this:
 *  <pre class="javascript">
 *   _createChildControlImpl: function(id) {
 *      var control;
 *
 *      switch(id) {
 *        ...
 *      }
 *      if (!control) {
 *        control = this.processHooks("after", "_createChildControlImpl", id);
 *      }
 *
 *      return control || this.base(arguments, id);
 *   }
 *  </pre>
 */
qx.Mixin.define("gosa.util.MMethodChaining", {

  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */
  members : {
    __hooks: null,

    /**
     * Add a method hook. Usually the callbacks should not return anything. If it does
     * the processor stops at that point and returns the value, other callbacks in that chain
     * are not executed in that case.
     *
     * @param type {String} 'before' or 'after'
     * @param method {String} original method this hook id added to
     * @param callback {Function} callback to be called as hook
     * @param context {Object}
     * @return {String} hook id
     */
    addHook: function(type, method, callback, context) {
      if (!this.__hooks) {
        this.__hooks = {
          before: {},
          after: {}
        };
      }
      if (qx.core.Environment.get('qx.debug')) {
        this.assertKeyInMap(type, this.__hooks);
      }
      if (!this.__hooks[type][method]) {
        this.__hooks[type][method] = [[callback, context]];
      } else {
        this.__hooks[type][method].push([callback, context]);
      }
      return type+"|"+method+"|"+this.__hooks[type][method].length-1;
    },

    /**
     * Removes a method hook by the given id
     * @param id {String} Hook id
     * @return {Boolean} True if the hook has been deleted successfully
     */
    removeHook: function(id) {
      var parts = id.split("|");
      return this.__hooks[parts[0]][parts[1]].splice([parts[2]], 1).length === 1;
    },

    /**
     * Process the hooks for a given method and type.
     * This method requires the arguments type, method. All additions arguments are passed to the
     * callback function.
     *
     * <h3>Hint:</h3>
     * Please keep in mind that if one of the hooks returns a value the processor stops at that point
     * and returns that value. This behaviour is useful to allow child controls to be created by Mixins.
     * You can add an "after" hook to the main classes "_createChildControlImpl" method and once one of the
     * processed hooks returns a child control, the processor stops and returns that one.
     *
     * @return {var|null}
     */
    processHooks: function() {
      if (!this.__hooks || !this.__hooks[arguments[0]][arguments[1]]) {
        return;
      }
      var type = [].splice.call(arguments, 0, 1);
      var method = [].splice.call(arguments, 0, 1);
      var args = arguments;
      var result = null;
      this.__hooks[type][method].some(function(entry) {
        result = entry[0].apply(entry[1], args);
        // break if a hook returns something
        if (result) {
          return true;
        }
      }, this);
      return result;
    }
  }
});