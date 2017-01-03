/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 *
 */
qx.Class.define("gosa.view.Dashboard", {
  extend : qx.ui.tabview.Page,
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/dashboard");
    this._setLayout(new qx.ui.layout.VBox());
    this.__layout = new qx.ui.layout.Grid(5, 5);
    this.__patchedThemes = {};

    this.addListenerOnce("appear", this.draw, this);

    this.addListener("longtap", function() {
      this.setEditMode(true);
    }, this);
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    __registry: {},

    registerWidget: function(widgetClass, options) {
      qx.core.Assert.assertTrue(qx.Interface.classImplements(widgetClass, gosa.plugins.IPlugin),
                                widgetClass+" does not implement the gosa.plugins.IPlugin interface");
      qx.core.Assert.assertString(widgetClass.NAME, widgetClass+" has no static NAME constant");

      this.__registry[widgetClass.NAME.toLowerCase()] = {
        clazz: widgetClass,
        options: options
      };
    },

    getWidgetRegistry: function() {
      return this.__registry;
    }
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-tabview-page"
    },

    columns : {
      check: "Number",
      init: 2
    },

    editMode: {
      check: "Boolean",
      init: false,
      event: "changeEditMode",
      apply: "_applyEditMode"
    },

    /**
     * Flag to determine modifications during editing mode
     */
    modified: {
      check: "Boolean",
      init: false,
      event: "changeModified"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __layout: null,
    __settings: null,
    __patchedThemes : null,
    __toolbarButtons: null,

    // property apply
    _applyEditMode: function(value) {
      if (value) {
        this.getChildControl("toolbar").show();
      } else {
        this.getChildControl("toolbar").exclude()
      }
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "toolbar":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(5, "center"));
          control.exclude();
          this.__fillToolbar(control);
          this._addAt(control, 0);
          break;

        case "board":
          control = new qx.ui.container.Composite(this.__layout);
          this._addAt(control, 1);
          break;
      }

      return control || this.base(arguments, id);
    },

    __fillToolbar: function(toolbar) {
      this.__toolbarButtons = {};

      // add button
      var widget = new qx.ui.form.Button(this.tr("Add"), "@Ligature/plus");
      widget.setEnabled(false);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("execute", function() {

      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["add"] = widget;

      // delete button
      var widget = new qx.ui.form.Button(this.tr("Delete"), "@Ligature/trash");
      widget.setDroppable(true);
      widget.setEnabled(false);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("drop", function(ev) {
        var target = ev.getRelatedTarget();
        target.destroy();
        this.setModified(true);
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["delete"] = widget;

      // abort editing
      widget = new qx.ui.form.Button(this.tr("Abort"), "@Ligature/undo");
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("execute", function() {
        this.setEditMode(false);
        this.refresh();
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["cancel"] = widget;

      // finish editing
      widget = new qx.ui.form.Button(this.tr("Save"), "@Ligature/check");
      widget.setEnabled(false);
      this.addListener("changeModified", function(ev) {
        widget.setEnabled(ev.getData() === true);
      }, this);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("execute", function() {
        this.setEditMode(false);
        this.save();
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["save"] = widget;
    },

    draw: function() {
      for (var i=0; i<this.getColumns(); i++) {
        this.__layout.setColumnFlex(i, 1);
      }

      // load dashboard settings from backend
      gosa.io.Rpc.getInstance().cA("loadUserPreferences", "dashboard")
      .then(function(result) {
        if (!result.length) {
          // default dashboard
          result = [{"widget":"Activities","layoutProperties":{"column":0,"row":1},"settings":{}},{"widget":"Activities","layoutProperties":{"column":1,"row":1},"settings":{"backgroundColor":"#DDDDDD"}},{"widget":"Search","layoutProperties":{"column":0,"colSpan":2,"row":0},"settings":{}}];
        }
        if (result.length) {
          this.__settings = result;
          this.refresh();
        }
      }, this);
    },

    refresh: function(skipCleanup) {
      var row=0;
      var col=0;
      console.log(this.getChildControl("board").getChildren().length);
      if (!skipCleanup && this.getChildControl("board").getChildren().length > 0) {
        this.getChildControl("board").removeAll();
        // re-build in next animation frame
        qx.bom.AnimationFrame.request(qx.lang.Function.curry(this.refresh, true), this);
        return;
      }

      var maxColumns = this.getColumns();
      var registry = gosa.view.Dashboard.getWidgetRegistry();
      this.__settings.forEach(function(entry) {
        var widgetName = entry.widget.toLowerCase();
        if (!registry[widgetName]) {
          this.warn("%s dashboard widget not registered", entry.widget);
        }
        else {
          var options = registry[widgetName].options;
          if (options && options['theme'] && !this.__patchedThemes[widgetName]) {
            for (var key in options['theme']) {
              if (key === "meta") {
                this.debug("patching meta theme "+options['theme'][key]);
                qx.Theme.patch(gosa.theme.Theme, options['theme'][key]);
              }
              else {
                this.debug("patching theme "+options['theme'][key]);
                qx.Theme.patch(gosa.theme[qx.lang.String.firstUp(key)], options['theme'][key]);
              }
            }
            this.__patchedThemes[widgetName] = true;
          }
          var widget = new registry[widgetName].clazz();
          if (entry.settings) {
            widget.configure(entry.settings);
          }
          widget.draw();
          this.bind("editMode", widget, "editMode");
          widget.addListener("dragstart", this._onDragStart, this);
          widget.addListener("dragend", this._onDragEnd, this);
          this.getChildControl("board").add(widget, entry.layoutProperties);
          col++;
          if (col >= maxColumns) {
            col = 0;
            row++;
          }
        }
      }, this);
    },

    _onDragStart: function() {
      this.__toolbarButtons['delete'].setEnabled(true);
    },

    _onDragEnd: function() {
      this.__toolbarButtons['delete'].setEnabled(false);
    },

    /**
     * Save the current dashboard settings to the backend
     */
    save: function() {
      // Save settings back to the user model
      if(gosa.Session.getInstance().getUser()) {
        // collect information
        var settings = [];
        this.getChildControl("board").getChildren().forEach(function(widget) {
          settings.push({
            widget: widget.constructor.NAME,
            layoutProperties: widget.getLayoutProperties(),
            settings: widget.getConfiguration()
          })
        }, this);
        gosa.io.Rpc.getInstance().cA("saveUserPreferences", "dashboard", settings)
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error.message).open();
        });
      }
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this.__layout = null;
    Object.getOwnPropertyNames(this.__toolbarButtons).forEach(function(name) {
      this.__toolbarButtons[name].dispose();
    }, this);
    this.__toolbarButtons = null;
  }
});
