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

/**
 * Controller for actions that can be done on the object (e.g. change password).
 */
qx.Class.define("gosa.data.controller.Actions", {

  extend : qx.core.Object,
  implement: gosa.data.controller.IAction,

  /**
   * @param object {gosa.proxy.Object}
   * @param widget {gosa.ui.widgets.ObjectEdit}
   */
  construct : function(object, widget) {
    this.base(arguments);
    qx.core.Assert.assertInstance(object, gosa.proxy.Object);
    qx.core.Assert.assertInstance(widget, gosa.ui.widgets.ObjectEdit);
    this.__object = object;
    this.__widget = widget;
  },

  members : {
    __object : null,
    __widget : null,

    // overridden
    allowMethodSelection: function() {
      return true;
    },

    /**
     * Returns the dn of the object.
     *
     * @return {String | null}
     */
    getDn : function() {
      return this.__object.dn;
    },

    /**
     * Returns the uuid of the object.
     *
     * @return {String | null}
     */
    getUuid : function() {
      return this.__object.uuid;
    },

    /**
     * Returns the value of the attribute of the object.
     *
     * @param attributeName {String} Name of the desired attribute
     * @return {qx.data.Array | null}
     */
    getAttributeValue : function(attributeName) {
      qx.core.Assert.assertString(attributeName);

      if (qx.Class.hasProperty(this.__object.constructor, attributeName)) {
        return this.__object.get(attributeName);
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
      var result;
      if (this.__object.hasOwnProperty(property)) {
        result = this.__object[property];
      } else {
        result = this.__object.get(property);
      }
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
      return this.__object.callMethod.apply(this.__object, arguments);
    },

    /**
     * Checks if the method is available on the object.
     *
     * @param methodName {String} Name of the Method
     * @return {Boolean}
     */
    hasMethod : function(methodName) {
      return qx.lang.Type.isFunction(this.__object[methodName]);
    },

    /**
     * Find the current password method saved in the object.
     *
     * @return {String | null} The current password method
     */
    getPasswordMethod : function() {
      if (!this.__object) {
        return null;
      }

      var methods = this.__object.getPasswordMethod();
      if (methods.getLength() > 0) {
        return methods.getItem(0);
      }
      return null;
    },

    /**
     * Getter for the internal object.
     *
     * @return {gosa.proxy.Object}
     */
    getObject: function() {
      return this.__object;
    },

    /**
     * Getter for the widget that edits the object.
     *
     * @return {gosa.ui.widgets.ObjectEdit}
     */
    getWidget : function() {
      return this.__widget;
    },

    /**
     * Move the object to a new DN
     *
     * @param newDn {String} new dn the object should be moved to
     * @return {qx.Promise}
     */
    move: function(newDn) {
      qx.core.Assert.assertString(newDn);
      return this.__object.move(newDn, true);
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
      return this.__object.changePasswordMethod(method, password);
    },

    /**
     * Change the password recovery answers.
     *
     * @param data {String} stringified json map (Answer index (key) => Answer (value))
     * @return {qx.Promise}
     */
    changePasswordRecoveryAnswers: function(data) {
      return this.__object.changePasswordRecoveryAnswers(data);
    },

    /**
     * Sets a new samba password.
     *
     * @param password {String} The password to save (not encoded)
     * @return {qx.Promise}
     */
    setSambaPassword : function(password) {
      qx.core.Assert.assertString(password);
      return this.__object.changeSambaPassword(password);
    },

    /**
     * Requests the current two-factor authentification method from the backend.
     * @return {qx.Promise}
     */
    getTwoFactorMethod : function() {
      return this.__object.getTwoFactorMethod();
    },

    /**
     * Saves a two-factor method.
     *
     * @param method {String} The method that shall be setPassword
     * @param password {String ? null} Optional password (only needed when two-factor was set before)
     * @return {qx.Promise}
     */
    setTwoFactorMethod : function(method, password) {
      if (method) {
        qx.core.Assert.assertString(method);
      }
      return this.__object.changeTwoFactorMethod(method, password);
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
      return this.__object.finishU2FRegistration(data);
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
      return this.__object.notify(subject, message);
    }
  },

  destruct : function() {
    this.__object = null;
    this.__widget = null;
  }
});
