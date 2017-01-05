/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Controller for actions that can be done on the object (e.g. change password).
 */
qx.Class.define("gosa.data.ActionController", {

  extend : qx.core.Object,

  /**
   * @param objectEditController {gosa.data.ObjectEditController}
   */
  construct : function(objectEditController) {
    this.base(arguments);
    qx.core.Assert.assertInstance(objectEditController, gosa.data.ObjectEditController);
    this._obj = objectEditController.getObject();
  },

  members : {
    _obj : null,

    /**
     * Returns the dn of the object.
     *
     * @return {String | null}
     */
    getDn : function() {
      return this._obj.dn;
    },

    /**
     * Returns the uuid of the object.
     *
     * @return {String | null}
     */
    getUuid : function() {
      return this._obj.uuid;
    },

    /**
     * Returns the value of the attribute of the object.
     *
     * @param attributeName {String} Name of the desired attribute
     * @return {qx.data.Array | null}
     */
    getAttributeValue : function(attributeName) {
      qx.core.Assert.assertString(attributeName);

      if (qx.Class.hasProperty(this._obj.constructor, attributeName)) {
        return this._obj.get(attributeName);
      }
      return null;
    },

    /**
     * Returns the value of a property of the object.
     *
     * @param property {String} Name of the desired property
     * @return {Var | null} The value of the property; null if not found
     */
    getProperty : function(property) {
      qx.core.Assert.assertString(property);
      var result = this._obj[property];
      return result === undefined ? null : result;
    },

    /**
     * Calls the given method on the object.
     *
     * @param methodName {String} Name of the method
     * @return {qx.Promise}
     */
    callMethod : function(methodName) {
      qx.core.Assert.assertString(methodName);
      return this._obj.callMethod.apply(this._obj, arguments);
    },

    /**
     * Find the current password method saved in the object.
     *
     * @return {String | null} The current password method
     */
    getPasswordMethod : function() {
      if (!this._obj) {
        return null;
      }

      var methods = this._obj.getPasswordMethod();
      if (methods.getLength() > 0) {
        return methods.getItem(0);
      }
      return null;
    },

    /**
     * Set the new password.
     *
     * @param method {String} The method to store the password (e.g. "MD5")
     * @param password {String} The password to save (not encoded)
     * @return {qx.Promise}
     */
    setPassword : function(method, password) {
      qx.core.Assert.assertString(method);
      qx.core.Assert.assertString(password);
      return this._obj.changePasswordMethod(method, password);
    },

    /**
     * Sets a new samba password.
     *
     * @param password {String} The password to save (not encoded)
     * @return {qx.Promise}
     */
    setSambaPassword : function(password) {
      qx.core.Assert.assertString(password);
      return this._obj.changeSambaPassword(password);
    },

    /**
     * Requests the current two-factor authentification method from the backend.
     * @return {qx.Promise}
     */
    getTwoFactorMethod : function() {
      return this._obj.getTwoFactorMethod();
    },

    /**
     * Saves a two-factor method.
     *
     * @param method {String} The method that shall be setPassword
     * @param password {String ? null} Optional password (only needed when two-factor was set before)
     * @return {qx.Promise}
     */
    setTwoFactorMethod : function(method, password) {
      qx.core.Assert.assertString(method);
      return this._obj.changeTwoFactorMethod(method, password);
    },

    /**
     * Finished the two-factor registration process.
     *
     * @param data {String ? undefined} Optional data; depends on the actual method
     * @return {qx.Promise}
     */
    finishU2FRegistration : function(data) {
      if (data) {
        qx.core.Assert.assertString(data);
      }
      return this._obj.finishU2FRegistration(data);
    },

    /**
     * Sends a message to the object.
     *
     * @param subject {String} Subject of the message
     * @param message {String} The actual message
     * @return {qx.Promise}
     */
    sendMessage : function(subject, message) {
      qx.core.Assert.assertString(subject);
      qx.core.Assert.assertString(message);
      return this._obj.notify(subject, message);
    }
  }
});
