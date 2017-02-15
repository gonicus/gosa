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
 * Dialog to request the user if dependent extensions shall be retracted in addition to the extension the user
 * originally selected.
 */
qx.Class.define("gosa.ui.dialogs.RetractDependencies", {
  extend : gosa.ui.dialogs.Dialog,

  /**
   * @param extension {String} The extension the user originally wants to retract
   * @param dependencies {Array} Other extensions (as String) that are dependent from the original extension
   */
  construct : function(extension, dependencies) {
    qx.core.Assert.assertString(extension);
    qx.core.Assert.assertArray(dependencies);

    this.base(arguments, this.trn("Dependent extension", "Dependent extensions", dependencies.length));

    this.setWidth(400);
    this.setAutoDispose(true);

    this._extension = extension;
    this._dependencies = dependencies;

    this._initWidgets();
  },

  events : {
    "ok": "qx.event.type.Event"
  },

  properties : {
    //overridden
    appearance : {
      refine : true,
      init : "window-warning"
    }
  },

  members : {
    _buttonAppearance : "button-warning",
    _extension : "",
    _dependencies : null,
    _numberOfNames : 0,
    _list : "",

    _initWidgets : function() {
      this._createDependencyList();

      var messageLabel = new qx.ui.basic.Label(this._getListMessage() + this._getQuestion());
      messageLabel.set({
        rich : true,
        wrap : true
      });
      this.addElement(messageLabel);

      this._createAndAddButtons();
    },

    _createDependencyList : function() {
      this._list = "<ul>";
      this._dependencies.forEach(function(dependency) {
        var names = this._getTranslatedExtension(dependency);
        names.forEach(function(name) {
          this._numberOfNames++;
          this._list += "<li><b>" + name + "</b></li>";
        }, this);
      }, this);
      this._list += "</ul>";
    },

    /**
     * Finds all translated names for an extension; one extension might have several names. If no translation is
     * found, it returns the original extension name as a fallback.
     *
     * @param extension {String}
     * @return {Array} List of strings
     */
    _getTranslatedExtension : function(extension) {
      qx.core.Assert.assertString(extension);
      var config = gosa.Cache.extensionConfig[extension];
      return config && config.title ? [config.title] : [extension];
    },

    _getListMessage : function() {
      return this.trn(
        "To retract the <b>%1</b> extension from this object, the following additional extension needs to be removed: %2",
        "To retract the <b>%1</b> extension from this object, the following additional extensions need to be removed: %2",
        this._numberOfNames, this._getTranslatedExtension(this._extension).join(', '), this._list
      );
    },

    _getQuestion : function() {
      return this.trn(
        "Do you want the dependent extension to be removed?",
        "Do you want the dependent extensions to be removed?",
        this._dependencies.length
      );
    },

    _createAndAddButtons : function() {
      var ok = gosa.ui.base.Buttons.getOkButton();
      ok.setAppearance("button-primary");
      ok.addListener("execute", this._onOkExecute, this);
      this.addButton(ok);

      var cancel = gosa.ui.base.Buttons.getCancelButton();
      cancel.setAppearance(this._buttonAppearance);
      cancel.addListener("execute", this.close, this);
      this.addButton(cancel);
    },

    _onOkExecute : function() {
      this.fireEvent("ok");
      this.close();
    }
  },

  destruct : function() {
    this._dependencies = null;
  }
});
