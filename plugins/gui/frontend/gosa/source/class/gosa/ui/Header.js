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

qx.Class.define("gosa.ui.Header", {
  extend: qx.ui.container.Composite,
  type: "singleton",

  construct: function() {
    this.base(arguments);
    this.setLayout(new qx.ui.layout.HBox());

    this._createChildControl("logo");
    this._createChildControl("windows");
    this._createChildControl("user");
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "changeEditMode": "qx.event.type.Event"
  },

  properties: {

    appearance: {
      refine: true,
      init: "title-bar"
    },
  
    loggedInName: {
      init: "",
      check: "String",
      event: "_changeLoggedInName",
      nullable: true,
      apply: "_applyLoggedInName"
    },

    imageURL: {
      init: "",
      check: "String",
      event: "_changeImageURL",
      nullable: true,
      apply: "_applyImageURL"
    }
  },

  members: {
    _listController: null,

    _createChildControlImpl: function(id) {
      var control;
      switch(id) {

        case "logo":
          control = new qx.ui.basic.Atom("GOsa", "gosa/images/logo.svg");
          this.add(control);
          break;

        case "user":
          control = new qx.ui.form.Button(this.tr("Menu"));
          var menu = this.__getMenu();
          menu.setOpener(control);
          control.addListener("execute", menu.open, menu);
          this.add(control);
          break;

        case "windows":
          control = new qx.ui.form.List(true);
          control.set({
            decorator: null,
            selectionMode: "single"
          });
          this.add(control, {flex: 1});
          this._listController = new qx.data.controller.List(null, control);
          this._listController.setDelegate(this.__getWindowDelegate());
          this._listController.setModel(gosa.data.controller.Window.getInstance().getWindows());
          break;

      }

      return control || this.base(arguments, id);
    },

    __getWindowDelegate: function() {
      return {

        createItem: function() {
          return new gosa.ui.form.WindowListItem();
        },

        bindItem: function(controller, item, index) {
          controller.bindProperty("[1]", "object", null, item, index);
          controller.bindProperty("[0]", "window", null, item, index);
          controller.bindProperty("[0].active", "selected", null, item, index);
        }
      }
    },

    __getMenu: function() {
      var menu = new qx.ui.menu.Menu();
      var changePw = new qx.ui.menu.Button(this.tr("Change my password"), "@Ligature/key/22");
      changePw.addListener("execute", function() {
        gosa.proxy.ObjectFactory.openObject(gosa.Session.getInstance().getDn())
        .then(function(obj) {
          var controller = new gosa.data.controller.Actions(obj);
          var dialog = new gosa.ui.dialogs.actions.ChangePasswordDialog(controller);
          dialog.addListener("close", function() {
            return obj.close();
          }, this);
          dialog.open();
          return null;
        }, this)
        .catch(function(exc) {
          (new gosa.ui.dialogs.Error(exc)).open();
        }, this);

      }, this);
      menu.add(changePw);

      var edit = new qx.ui.menu.Button(this.tr("Edit my profile"), "@Ligature/edit/22");
      edit.addListener("execute", function(){
        document.location.href = gosa.Tools.createActionUrl('openObject', gosa.Session.getInstance().getUuid());
      }, this);
      menu.add(edit);

      menu.add(new qx.ui.menu.Separator());

      var logout = new qx.ui.menu.Button(this.tr("Logout"), "@Ligature/logout");
      logout.getChildControl("icon").set({
        width: 22,
        scale: true
      });
      logout.addListener("execute", function(){
        gosa.Session.getInstance().logout();
      }, this);
      menu.add(logout);

      return menu;
    },

    _applyLoggedInName: function(value){
      if(value === null){
        this.getChildControl("user").setLabel(this.tr("Menu"));
      }else{
        this.getChildControl("user").setLabel(value);
      }
    },

    _applyImageURL: function(value) {
      if (value === "" || value === null) {
        this.getChildControl("user").resetIcon();
      }
      else {
        this.getChildControl("user").setIcon(value);
      }
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._disposeObjects("_listController");
  }
});
