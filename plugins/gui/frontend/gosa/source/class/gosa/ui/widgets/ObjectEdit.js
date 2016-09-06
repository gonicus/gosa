/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Container showing several tabs - all necessary for displaying forms for editing an object.
 */
qx.Class.define("gosa.ui.widgets.ObjectEdit", {

  extend: qx.ui.container.Composite,

  /**
   * @param templates {Array} List of hash maps in the shape {extension: <name>, template: <template>}; each appears
   *   in its own tab
   */
  construct: function(templates) {
    this.base(arguments);
    qx.core.Assert.assertArray(templates);
    this._templates = templates;

    this._contexts = [];

    this.setLayout(new qx.ui.layout.VBox());
    this._initWidgets();
  },

  properties : {
    controller: {
      check : "gosa.data.ObjectEditController",
      init : null,
      apply : "_applyController"
    }
  },

  members : {

    _templates : null,
    _tabView : null,
    _toolMenu : null,
    _buttonPane : null,
    _contexts : null,
    _okButton : null,

    /**
     * Retrieve all contexts this widget is showing.
     *
     * @return {Array} A (maybe empty) array of {@link gosa.engine.Context} objects
     */
    getContexts : function() {
      return this._contexts;
    },

    _applyController : function(value, old) {
      if (old) {
        value.removeRelatedBindings(this._okButton);
      }

      if (value) {
        value.bind("modified", this._okButton, "enabled");
      }
    },

    _initWidgets : function() {
      this._createTabView();
      this._createTabPages();
      this._createToolmenu();
      this._createButtons();
    },

    _createTabView : function() {
      this._tabView = new gosa.ui.tabview.TabView();
      this._tabView.getChildControl("bar").setScrollStep(150);
      this.add(this._tabView, {flex : 1});
    },

    _createTabPages : function() {
      this._templates.forEach(function(templateObj) {
        var template = templateObj.template;
        var tabPage = new qx.ui.tabview.Page();
        tabPage.setLayout(new qx.ui.layout.VBox());

        var context = new gosa.engine.Context(template, tabPage, templateObj.extension);
        this._contexts.push(context);
        this._tabView.add(context.getRootWidget());
      }, this);
    },

    _createToolmenu : function() {
      this._toolMenu = new qx.ui.menu.Menu();
      this._tabView.getChildControl("bar").setMenu(this._toolMenu);

      this._createActionButtons();
    },

    _createActionButtons : function() {
      var allActionEntries = {};
      var actionEntries, key;

      // collect action menu entries
      this._contexts.forEach(function(context) {
        actionEntries = context.getActions();
        for (var name in actionEntries) {
          if (actionEntries.hasOwnProperty(name)) {
            qx.core.Assert.assertFalse(allActionEntries.hasOwnProperty(name), "Duplicate action name: '" + name + "'");
            allActionEntries[name] = actionEntries[name];
          }
        }
      });

      // sort by name
      var sorted = [];
      for(key in allActionEntries) {
        sorted[sorted.length] = key;
      }
      sorted.sort();

      // add menu entries to widget
      sorted.forEach(function(key) {
        this._toolMenu.add(allActionEntries[key]);
      }, this);
    },

    _createButtons : function() {
      var paneLayout = new qx.ui.layout.HBox();
      paneLayout.set({
        spacing: 4,
        alignX : "right",
        alignY : "middle"
      });
      this._buttonPane = new qx.ui.container.Composite(paneLayout);
      this._buttonPane.setMarginTop(11);

      this.add(this._buttonPane);
      this._createOkButton();
      this._createCancelButton();
    },

    _createOkButton : function() {
      var button = this._okButton = gosa.ui.base.Buttons.getOkButton();
      button.set({
        enabled : false,
        tabIndex : 30000
      });
      button.addState("default");
      this._buttonPane.add(button);

      button.addListener("execute", this._onOk, this);
    },

    _createCancelButton : function() {
      var button = gosa.ui.base.Buttons.getCancelButton();
      button.setTabIndex(30001);
      this._buttonPane.add(button);

      button.addListener("execute", this._onCancel, this);
    },

    /**
     * @return {qx.ui.window.Window | null}
     */
    _getParentWindow : function() {
      var parent = this;
      do {
        parent = parent.getLayoutParent();
        if (parent instanceof qx.ui.window.Window) {
          return parent;
        }
      } while (parent);
      return null;
    },

    _onOk : function() {
      console.warn("TODO: save changed values");
      this._getParentWindow().close();
    },

    _onCancel : function() {
      if (this.getController() && this.getController().isModified()) {
        this._createConfirmDialog();
      }
      else {
        this._getParentWindow().close();
      }
    },

    _createConfirmDialog : function() {
      var dialog = new gosa.ui.dialogs.Dialog(this.tr("Unsaved changes"));
      dialog.setAutoDispose(true);
      dialog.addElement(new qx.ui.basic.Label(this.tr("There are unsaved changes. Are you sure to really abort?")));

      var okButton = new qx.ui.form.Button(this.tr("Ok"));
      okButton.addListener("execute", function() {
        this._getParentWindow().close();
        dialog.close();
      }, this);
      dialog.addButton(okButton);

      var cancelButton = new qx.ui.form.Button(this.tr("Cancel"));
      cancelButton.addListener("execute", dialog.close, dialog);
      dialog.addButton(cancelButton);

      dialog.open();
    }
  },

  destruct : function() {
    this._templates = null;
    qx.util.DisposeUtil.disposeArray("_contexts");
    this._disposeObjects("_okButton", "_toolMenu", "_buttonPane", "_tabView");
  }
});
