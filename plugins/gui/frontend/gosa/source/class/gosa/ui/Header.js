/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.Header", {
  extend: qx.ui.container.Composite,
  type: "singleton",

  construct: function() {
    this.base(arguments);
    this.setLayout(new qx.ui.layout.HBox());

    this._createChildControl("sandwich");
    this._createChildControl("windows");
  }, 

  properties: {

    appearance: {
      refine: true,
      init: "title-bar"
    },
  
    loggedInName: {
      init: "",
      check: "String",
      event: "_changedLoggedInName",
      nullable: true,
      apply: "_applyLoggedInName"
    }
  },

  members: {
    _listController: null,
    _logout: null,

    _createChildControlImpl: function(id) {
      var control;
      switch(id) {

        case "sandwich":
          control = new qx.ui.form.Button();
          control.setToolTip(new qx.ui.tooltip.ToolTip(this.tr("Menu")));
          var menu = this.__getSandwichMenu();
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
          control.addListener("changeSelection", this._onChangeSelection, this);
          this.add(control, {flex: 1});
          this._listController = new qx.data.controller.List(null, control);
          this._listController.setDelegate(this.__getWindowDelegate());
          this._listController.setModel(gosa.data.WindowController.getInstance().getWindows());
          break;

        case "search":
          var command = new qx.ui.command.Command("enter");
          var button = new qx.ui.form.Button("", "@Ligature/search", command);
          button.set({
            show: "icon",
            center: true,
            decorator: null
          });
          button.getChildControl("icon").set({
            width: 35,
            height: 35,
            scale: true
          });
          this.add(button);
          control = new qx.ui.form.TextField('');
          control.setPlaceholder(this.tr("Please enter your search..."));
          control.bind("visibility", button, "visibility");
          control.hide();
          this.add(control);
          new qx.util.DeferredCall(function() {
            var searchView = gosa.view.Search.getInstance();
            button.addListener("execute", function() {
              gosa.Application.showPage("search");
              searchView.doSearch();
            }, this);
            control.addListener("changeValue", function(ev) {
              searchView.searchField.setValue(ev.getData());
            }, this);
          }, this).schedule();
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
        }
      }
    },

    _onChangeSelection: function(ev) {
      var selection = ev.getData();
      if (selection.length > 0) {
        var win = selection[0].getWindow();
        win.show();
        win.setActive(true);
      }
    },

    __getSandwichMenu: function() {
      var menu = new qx.ui.menu.Menu();
      var changePw = new qx.ui.menu.Button(this.tr("Change my password"));
      changePw.addListener("execute", function() {

      }, this);
      menu.add(changePw);

      var edit = new qx.ui.menu.Button(this.tr("Edit my profile"));
      edit.addListener("execute", function(){
        document.location.href = gosa.Tools.createActionUrl('openObject', gosa.Session.getInstance().getUuid());
      }, this);
      menu.add(edit);


      var logout = this._logout = new qx.ui.menu.Button(this.tr("Logout"), "@Ligature/logout");
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
        this._logout.setLabel(this.tr("Logout"));
      }else{
        this._logout.setLabel(this.tr("Logout") + ": " + value);
      }
    },

    /*
    *****************************************************************************
       DESTRUCTOR
    *****************************************************************************
    */
    destruct : function() {
      this._disposeObjects("_logout");
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
