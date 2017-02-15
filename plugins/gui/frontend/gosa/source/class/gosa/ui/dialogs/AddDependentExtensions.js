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
* Dialog that lists all extensions that are necessary, yet missing. The user can choose if to add the dependencies or to
* remove the extensions that are lacking them.
*/
qx.Class.define("gosa.ui.dialogs.AddDependentExtensions", {
  extend: gosa.ui.dialogs.Confirmation,

  /**
   * @param extensionMap {Object} Keys: name of extension, value: array of names of its dependencies
   */
  construct: function(extensionMap) {
    this.base(arguments, this.tr("Add missing extensions"));
    this.setAutoDispose(true);
    qx.core.Assert.assertMap(extensionMap);

    this._okButton.setLabel(this.tr("Add"));
    this._cancelButton.setLabel(this.tr("Remove"));

    this.setMaxWidth(600);

    this.__addMessage(extensionMap);
    this.__createExtensionListContainer();
    this.__addExtensionList(extensionMap);
  },

  members : {

    __extensionListContainer : null,

    __addMessage : function() {
      var message = this.tr("This object has extensions attached, which are missing other extensions as their dependencies (see list below). Click '%1' to add the missing extensions or click '%2' to remove those with broken dependencies.", this.tr("Add"), this.tr("Remove"));
      var label = new qx.ui.basic.Label(message);
      label.set({
        rich : true,
        wrap : true
      });
      this.addElement(label);

      message = this.tr("List of extensions and their missing dependencies:");
      this.addElement(new qx.ui.basic.Label(message));
    },

    __createExtensionListContainer : function() {
      var layout = new qx.ui.layout.VBox();
      this.__extensionListContainer = new qx.ui.container.Composite(layout);
      this.__extensionListContainer.setMarginLeft(20);
      this.addElement(this.__extensionListContainer);
    },

    /**
     * @param extensionMap {Object} Map as described in constructor
     */
    __addExtensionList : function(extensionMap) {
      gosa.util.Object.iterate(extensionMap, function(extName, exts) {
        this.__addBoldListLabel(extName);
        this.__beginList();
        exts.forEach(this.__addDependencyLabel, this);
        this.__endList();
      }, this);
    },

    __addBoldListLabel: function(extName) {
      var label = new qx.ui.basic.Label("<strong>" + extName + "</strong> " + this.tr("depends on"));
      label.setRich(true);
      this.__extensionListContainer.add(label);
    },

    __addDependencyLabel : function(extName) {
      var label = new qx.ui.basic.Label("<li>" + extName + "</li>");
      label.setRich(true);
      this.__extensionListContainer.add(label);
    },

    __beginList : function() {
      var label = new qx.ui.basic.Label("<ul>");
      label.setRich(true);
      this.__extensionListContainer.add(label);
    },

    __endList : function() {
      var label = new qx.ui.basic.Label("</ul>");
      label.setRich(true);
      this.__extensionListContainer.add(label);
    }
  },

  destruct : function() {
    this._disposeObjects("__extensionListContainer");
  }
});
