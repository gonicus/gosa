/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Customizable Dashboard view
 * 
 */
qx.Class.define("gosa.view.Dashboard", {
  extend : qx.ui.tabview.Page,
  type: "singleton",

  construct : function()
  {
    // Call super class and configure ourselfs
    this.base(arguments, "", "@Ligature/tile");
    this._setLayout(new qx.ui.layout.VBox());
    this.__gridLayout = new qx.ui.layout.Grid(5, 5);
    this.__columns = 6;
    this.__patchedThemes = {};

    this.addListener("appear", function() {
      if (!this.__drawn) {
        this.draw();
      }
    }, this);
    this.getChildControl("edit-mode");
    this.getChildControl("board").addListener("resize", this._onGridResize, this);

    this.addListener("longtap", function() {
      this.setEditMode(true);
    }, this);
    gosa.io.Sse.getInstance().addListener("pluginUpdate", this._onPluginUpdate, this);
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    __registry: {},
    __parts: {},
    __columns: null,
    __drawn: null,

    /**
     * Register a loaded dashboard widget for usage
     *
     * @param widgetClass {Class} Main widget class
     * @param options {Map} additional configuration options
     */
    registerWidget: function(widgetClass, options) {
      qx.core.Assert.assertTrue(qx.Interface.classImplements(widgetClass, gosa.plugins.IPlugin),
                                widgetClass+" does not implement the gosa.plugins.IPlugin interface");
      qx.core.Assert.assertString(options.displayName, "No 'displayName' property found in options");

      var entry = {
        clazz: widgetClass,
        options: options
      };

      var packageName = gosa.util.Reflection.getPackageName(widgetClass);

      var Env = qx.core.Environment;
      var sourceKey = packageName+".source";

      var sourceEnv = Env.get(sourceKey);
      if (!sourceEnv) {
        Env.add(sourceKey, "builtin");
      }

      if (sourceEnv === "part") {
        // plugin loaded from part
        delete this.__parts[packageName];
      }

      this.__registry[packageName] = entry;
    },

    getWidgetRegistry: function() {
      return this.__registry;
    },

    /**
     * Register an (unloaded) part that provides a dashboard widget
     * @param part {qx.ui.part.Part}
     */
    registerPart: function(part) {
      // generate the widget name from the part name
      var widgetName = qx.lang.String.firstUp(part.getName().replace("gosa.plugins.",""));
      qx.core.Environment.add(part.getName()+".source", "part");
      this.__parts[part.getName()] = widgetName;
    },

    getPartRegistry: function() {
      return this.__parts;
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
      init: "gosa-tabview-page-dashboard"
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
    },

    selectedWidget: {
      check: "gosa.plugins.AbstractDashboardWidget",
      nullable: true,
      apply: "_applySelectedWidget"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __gridLayout : null,
    __settings: null,
    __patchedThemes : null,
    __toolbarButtons: null,
    _createMenu : null,

    // property apply
    _applyEditMode: function(value) {
      var grid = this.__gridLayout;
      var board = this.getChildControl("board");
      var row, column, widget, lr, lc;

      if (value) {
        this.getChildControl("toolbar").show();
        this.getChildControl("board").addListener("tap", this._onTap, this);
        this.getChildControl("board").getChildren().forEach(function(child) {
          if (child instanceof gosa.plugins.AbstractDashboardWidget) {
            child.addListener("tap", this._onTap, this);
          }
        }, this);

        // add dropboxes to empty cells + one additional row
        for (row=1, lr = grid.getRowCount()+1; row < lr; row++) {
          for (column=0, lc = grid.getColumnCount(); column < lc; column++) {
            widget = grid.getCellWidget(row, column);
            if (widget instanceof qx.ui.core.Spacer) {
              widget.destroy();
              widget = null;
            }
            if (!widget) {
              board.add(new gosa.ui.core.GridCellDropbox(), {row: row, column: column});
            }
          }
        }
        qx.event.message.Bus.subscribe("gosa.dashboard.drop", this._onMove, this);
      } else {
        this.getChildControl("toolbar").exclude();
        this.getChildControl("board").getChildren().forEach(function(child) {
          if (child instanceof gosa.plugins.AbstractDashboardWidget) {
            child.removeListener("tap", this._onTap, this);
          }
        }, this);
        this.getChildControl("board").removeListener("tap", this._onTap, this);
        this.setSelectedWidget(null);
        this.setModified(false);

        // remove the grid dropboxes
        for (row=1, lr = grid.getRowCount()+1; row < lr; row++) {
          for (column=0, lc = grid.getColumnCount(); column < lc; column++) {
            widget = grid.getCellWidget(row, column);
            if (widget instanceof gosa.ui.core.GridCellDropbox) {
              widget.destroy();
            }
          }
        }
        qx.event.message.Bus.unsubscribe("gosa.dashboard.drop", this._onMove, this);
      }
    },

    _onMove: function(ev) {
      var data = ev.getData();
      var oldProps = qx.lang.Object.clone(data.widget.getLayoutProperties());
      var col;

      // free space
      for (col=data.props.column, l=data.props.column+oldProps.colSpan||1; col<l; col++) {
        var old = this.__gridLayout.getCellWidget(data.props.row, col);
        if (old && old !== data.widget) {
          old.destroy();
        }
      }

      data.widget.setLayoutProperties({row: data.props.row, column: data.props.column, colSpan: oldProps.colSpan, rowSpan: oldProps.rowSpan});

      // add placeholders on old widgets place
      var board = this.getChildControl("board");
      for (col=oldProps.column, l=oldProps.column+oldProps.colSpan||1; col<l; col++) {
        var cur = this.__gridLayout.getCellWidget(oldProps.row, col);
        if (!cur) {
          board.add(new gosa.ui.core.GridCellDropbox(), {
            row    : oldProps.row,
            column : col
          });
        }
      }
      this.setModified(true);
    },

    _onTap: function(ev) {
      if (ev.getCurrentTarget() instanceof gosa.plugins.AbstractDashboardWidget) {
        this.setSelectedWidget(ev.getCurrentTarget());
        ev.stopPropagation();
      } else {
        this.setSelectedWidget(null);
      }
    },

    /**
     * Recalculate grid column width/row height
     */
    _onGridResize: function() {
      var bounds = this.getChildControl("board").getBounds();
      var columnSize = Math.floor((bounds.width / this.__columns) - this.__gridLayout.getSpacingX());
      // apply size to columns
      for (var i=0, l = this.__gridLayout.getColumnCount(); i < l; i++) {
        this.__gridLayout.setColumnWidth(i, columnSize);
      }
    },

    _applySelectedWidget: function(value, old) {
      if (old) {
        old.removeState("selected");
      }
      if (value) {
        value.addState("selected");
        this.__toolbarButtons['delete'].setEnabled(true);
        this.__toolbarButtons['edit'].setEnabled(true);
      } else {
        this.__toolbarButtons['delete'].setEnabled(false);
        this.__toolbarButtons['edit'].setEnabled(false);
      }
    },

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "header":
          control = new qx.ui.container.Composite(new qx.ui.layout.Canvas());
          this._addAt(control, 0);
          break;

        case "edit-mode":
          control = new qx.ui.form.Button(null, "@Ligature/gear");
          control.setZIndex(1000);
          this.getChildControl("header").add(control, {top: 0, right: 0});
          control.addListener("execute", function() {
            this.toggleEditMode();
          }, this);
          break;

        case "toolbar":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(5, "center"));
          control.exclude();
          this.__fillToolbar(control);
          this.getChildControl("header").add(control, {edge: 0});
          break;

        case "board":
          control = new qx.ui.container.Composite(this.__gridLayout);
          this._addAt(control, 1, {flex: 1});
          break;
      }

      return control || this.base(arguments, id);
    },

    /**
     * Add buttons to the toolbar for the editing mode
     * @param toolbar {qx.ui.container.Composite} the toolbar
     */
    __fillToolbar: function(toolbar) {
      this.__toolbarButtons = {};

      // widget creation menu
      var menu = this._createMenu = new qx.ui.menu.Menu();
      var uploadButton = new com.zenesis.qx.upload.UploadMenuButton(this.tr("Upload"), "@Ligature/upload");
      uploadButton.setAppearance("icon-menu-button");

      gosa.io.Rpc.getInstance().cA("registerUploadPath", "widgets")
      .then(function(result) {
        var path = result[1];
        var uploader = new gosa.util.UploadMgr(uploadButton, path);
      }, this);
      menu.add(uploadButton);
      menu.add(new qx.ui.menu.Separator());

      var registry = gosa.view.Dashboard.getWidgetRegistry();
      Object.getOwnPropertyNames(registry).forEach(function(name) {
        var entry = registry[name];
        var button = new qx.ui.menu.Button(entry.options.displayName, entry.options.icon);
        button.setAppearance("icon-menu-button");
        button.setUserData("widget", name);
        menu.add(button);
        button.addListener("execute", this._createWidget, this);
      }, this);

      // add the unloaded parts (loaded parts are already in the registry
      var parts = gosa.view.Dashboard.getPartRegistry();
      Object.getOwnPropertyNames(parts).forEach(function(name) {
        var displayName = parts[name];
        var button = new qx.ui.menu.Button(displayName);
        button.setUserData("part", name);
        menu.add(button);
        button.addListener("execute", this._loadPart, this);
      }, this);

      // add the uploaded widgets which can be downloaded from the backend
      gosa.io.Rpc.getInstance().cA("getDashboardWidgets")
      .then(function(widgets) {
        widgets.forEach(function(widget) {
          if (!gosa.view.Dashboard.getWidgetRegistry()[widget.provides.namespace]) {
            var displayName = widget.info.name;
            var button = new qx.ui.menu.Button(displayName);
            button.setUserData("namespace", widget.provides.namespace);
            menu.add(button);
            button.addListener("execute", this._loadFromBackend, this);
          }
        }, this);
      }, this);

      // add button
      var widget = new qx.ui.form.MenuButton(this.tr("Add"), "@Ligature/plus", menu);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("appear", function(ev) {
        var element = ev.getTarget().getContentElement().getDomElement();
        element.ondrop = function(e) {
          gosa.util.DragDropHelper.getInstance().onHtml5Drop.call(gosa.util.DragDropHelper.getInstance(), e);
          element.ondragleave();
        };
        element.ondragleave = function() {
          var spec = {
            duration: 200,
            timing: "ease-in-out",
            keep: 100,
            keyFrames : {
              0: {
                scale : "1.2"
              },
              100: {
                scale : "1"
              }
            }
          };
          qx.bom.element.Animation.animate(element, spec);
          return false;
        };
        element.ondragover = function() {
          var spec = {
            duration: 200,
            timing: "ease-in-out",
            keep: 100,
            keyFrames : {
              0: {
                scale : "1"
              },
              100: {
                scale : "1.2"
              }
            }
          };
          qx.bom.element.Animation.animate(element, spec);
          return false;
        };
      }, this);
      gosa.util.DragDropHelper.getInstance().addListener("loaded", this._onExternalLoad, this);
      toolbar.add(widget);
      this.__toolbarButtons["add"] = widget;

      // edit button
      widget = new qx.ui.form.Button(this.tr("Edit"), "@Ligature/gear");
      widget.setDroppable(true);
      widget.setEnabled(false);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("tap", function() {
        if (this.getSelectedWidget()) {
          // open edit dialog
          var dialog = new gosa.ui.dialogs.EditDashboardWidget(this.getSelectedWidget());
          dialog.addListenerOnce("modified", function() {
            this.setModified(true);
          }, this);
          dialog.open();
        }
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["edit"] = widget;

      // delete button
      widget = new qx.ui.form.Button(this.tr("Delete"), "@Ligature/trash");
      widget.setDroppable(true);
      widget.setEnabled(false);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("tap", function() {
        if (this.getSelectedWidget()) {
          this.__deleteWidget(this.getSelectedWidget());
        }
      }, this);
      widget.addListener("drop", function(ev) {
        this.__deleteWidget(ev.getRelatedTarget());
      }, this);
      widget.addListener("dragover", function(ev) {
        var spec = {
          duration: 200,
          timing: "ease-in-out",
          keep: 100,
          keyFrames : {
            0: {
              scale : "1"
            },
            100: {
              scale : "1.2"
            }
          }
        };
        qx.bom.element.Animation.animate(ev.getTarget().getContentElement().getDomElement(), spec);
      }, this);
      widget.addListener("dragleave", function(ev) {
        var spec = {
          duration: 200,
          timing: "ease-in-out",
          keep: 100,
          keyFrames : {
            0: {
              scale : "1.2"
            },
            100: {
              scale : "1"
            }
          }
        };
        qx.bom.element.Animation.animate(ev.getTarget().getContentElement().getDomElement(), spec);
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["delete"] = widget;


      // clear dashboard
      widget = new qx.ui.form.Button(this.tr("Clear"), "@Ligature/clear");
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("execute", function() {
        this.getChildControl("board").removeAll();
        this.setModified(true);
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["clear"] = widget;

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
      widget.setEnabled(this.isModified());
      this.addListener("changeModified", function(ev) {
        this.__toolbarButtons['save'].setEnabled(ev.getData() === true);
      }, this);
      widget.setAppearance("gosa-dashboard-edit-button");
      widget.addListener("execute", function() {
        this.setEditMode(false);
        this.save();
      }, this);
      toolbar.add(widget);
      this.__toolbarButtons["save"] = widget;
    },

    __deleteWidget: function(widget) {
      var layoutProps = widget.getLayoutProperties();
      widget.destroy();
      this.setModified(true);
      // add spacer as replacement
      this.getChildControl("board").add(new qx.ui.core.Spacer(), layoutProps);
      if (this.getSelectedWidget() === widget) {
        this.setSelectedWidget(null);
      }
    },

    /**
     * Add a widget to the dashboard, triggered by the 'execute' event from an entry in the 'add' menu
     */
    _createWidget: function(ev) {
      var widgetName = "";
      if (qx.lang.Type.isString(ev)) {
        widgetName = ev.toLowerCase();
      } else {
        var button = ev.getTarget();
        widgetName = button.getUserData("widget");
      }
      var widgetData = gosa.view.Dashboard.getWidgetRegistry()[widgetName];
      var entry = {
        widget: widgetName
      };
      // find empty space in grid
      var placed = false;
      for(var row=1, l = this.__gridLayout.getRowCount(); row < l; row++) {
        for(var col=0, k = this.__gridLayout.getColumnCount(); col < k; col++) {
          if (col + widgetData.options.defaultColspan > this.__columns) {
            // not enough space in this row
            break;
          }
          var widget = this.__gridLayout.getCellWidget(row, col);
          if (widget instanceof qx.ui.core.Spacer) {
            // replace spacer
            entry.layoutProperties = widget.getLayoutProperties();
            widget.destroy();
            // break the outer loop
            placed = true;
            break;
          }
          else if (!widget) {
            // empty cell
            entry.layoutProperties = {
              row: row,
              column: col
            };
            // break the outer loop
            placed = true;
            break;
          }
        }
        if (placed) {
          break;
        }
      }
      if (!placed) {
        // add at the end
        entry.layoutProperties = {
          row    : row,
          column : 0
        };
      }
      entry.layoutProperties.colSpan = widgetData.options.defaultColspan || 3;
      this.__addWidget(entry);
      this.setModified(true);
    },

    /**
     * Load a widget plugin part and create the widget afterwards
     * @param ev {Event} execute event from button
     */
    _loadPart: function(ev) {
      var button = ev.getTarget();
      var partName = button.getUserData("part");
      var part = qx.io.PartLoader.getInstance().getPart(partName);
      if (part.getReadyState() === "initialized") {
        // load part
        qx.Part.require(partName, function() {
          // part is loaded
          this._createWidget(partName);
        }, this);
      }
    },

    /**
     * Load uploaded widget from backend
     * @param ev {Event} with widgets namespace as payload
     */
    _loadFromBackend: function(ev) {
      var button = ev.getTarget();
      var namespace = button.getUserData("namespace");
      var loader = new qx.util.DynamicScriptLoader(['/gosa/uploads/widgets/'+namespace+'/'+namespace+".js"]);
      loader.addListenerOnce("ready", function() {
        this._createWidget(namespace);
      }, this);
      loader.addListener('failed',function(e){
        var data = e.getData();
        this.error("failed to load "+data.script);
      });
      loader.start();
    },

    /**
     * Handle 'loaded' events from {gosa.util.DragDropHelper} to add uploaded widgets
     * @param ev {qx.event.type.Data} data event with widgets package name as payload
     */
    _onExternalLoad: function(ev) {
      this._createWidget(ev.getData());
    },

    /**
     * pre-filling with spacers to have a 12-col grid
     */
    __addFirstSpacerRow: function() {
      var board = this.getChildControl("board");
      for(var i=0; i<this.__columns; i++) {
        board.add(new qx.ui.core.Spacer(), {row: 0, column: i});
        this.__gridLayout.setColumnFlex(i, 1);
      }
    },

    /**
     * Loads the dashboard settings from the backend and creates it.
     */
    draw: function() {
      var board = this.getChildControl("board");
      this.__addFirstSpacerRow();

      // load dashboard settings from backend
      gosa.io.Rpc.getInstance().cA("loadUserPreferences", "dashboard")
      .then(function(result) {
        if (result.length) {
          this.__settings = result;
          var pluginsToLoad = this.__extractPluginsToLoad(result);
          var partsLoaded = pluginsToLoad.parts.length === 0;
          var scriptsLoaded = pluginsToLoad.scripts.length === 0;

          var done = function() {
            if (partsLoaded && scriptsLoaded) {
              this.refresh(true);
            }
          }.bind(this);
          if (pluginsToLoad.parts.length > 0) {
            qx.Part.require(pluginsToLoad.parts, function() {
              done();
            }, this);
          }
          if (pluginsToLoad.scripts.length > 0) {
            var loader = new qx.util.DynamicScriptLoader(pluginsToLoad.scripts);
            loader.addListenerOnce("ready", function() {
              scriptsLoaded = true;
              done();
            }, this);
            loader.start();
          } else {
            done();
          }
        }
        this.__drawn = true;
      }, this);
    },

    __extractPluginsToLoad: function(settings) {
      var partsToLoad = [];
      var scriptsToLoad = [];
      var loader = qx.io.PartLoader.getInstance();
      settings.forEach(function(widgetEntry) {
        if (widgetEntry.source === "part") {
          //check if part is already loaded
          var part = loader.getPart(widgetEntry.widget);
          if (part.getReadyState() === "initialized") {
            partsToLoad.push(widgetEntry.widget);
          }
        } else if (widgetEntry.source === "external") {
          scriptsToLoad.push('/gosa/uploads/widgets/'+widgetEntry.widget+"/"+widgetEntry.widget+".js");
        }
      }, this);
      return {parts: partsToLoad, scripts: scriptsToLoad};
    },

    /**
     * Refresh the dashboard. Removes all existing widgets (if there are any) and create new ones according to the current
     * configuration.
     *
     * @param skipCleanup {Boolean?} if true skip the cleanup step before re-creating
     */
    refresh: function(skipCleanup) {
      if (!skipCleanup && this.getChildControl("board").getChildren().length > 0) {
        this.getChildControl("board").removeAll();
        // re-build in next animation frame
        qx.bom.AnimationFrame.request(qx.lang.Function.curry(this.refresh, true), this);
        this.__addFirstSpacerRow();
        return;
      }
      if (this.__settings) {
        this.__settings.forEach(this.__addWidget, this);
      }
    },

    __addWidget: function(entry) {
      var registry = gosa.view.Dashboard.getWidgetRegistry();
      var widgetName = entry.widget;
      var widget;
      if (widgetName === "qx.ui.core.Spacer") {
        widget = new qx.ui.core.Spacer();
        this.getChildControl("board").add(widget, entry.layoutProperties);
        return widget;
      }
      else if (!registry[widgetName]) {
        this.warn(entry.widget+" dashboard widget not registered");
      }
      else {
        var options = registry[widgetName].options;
        if (options && options['theme'] && !this.__patchedThemes[widgetName]) {
          for (var key in options['theme']) {
            if (options['theme'].hasOwnProperty(key)) {
              if (key === "meta") {
                this.debug("patching meta theme " + options['theme'][key]);
                qx.Theme.patch(gosa.theme.Theme, options['theme'][key]);
              }
              else {
                this.debug("patching theme " + options['theme'][key]);
                qx.Theme.patch(gosa.theme[qx.lang.String.firstUp(key)], options['theme'][key]);
              }
            }
          }
          this.__patchedThemes[widgetName] = true;
        }
        //noinspection JSPotentiallyInvalidConstructorUsage
        widget = new registry[widgetName].clazz();
        if (entry.settings) {
          widget.configure(entry.settings);
        }
        widget.draw();
        this.bind("editMode", widget, "editMode");
        widget.addListener("dragstart", this._onDragStart, this);
        widget.addListener("dragend", this._onDragEnd, this);
        if (this.isEditMode()) {
          widget.addListener("tap", this._onTap, this);
          this.setSelectedWidget(widget);
        }
        widget.addListener("layoutChanged", function(ev) {
          this.__toolbarButtons['save'].setEnabled((ev.getData() === true));
        }, this);
        // remove spacers if there are any
        var colspan = entry.layoutProperties.colSpan||1;
        for(var c=entry.layoutProperties.column, l = c + colspan; c<l; c++) {
          var currentWidget = this.__gridLayout.getCellWidget(entry.layoutProperties.row, c);
          if (currentWidget instanceof qx.ui.core.Spacer) {
            currentWidget.destroy();
          }
        }
        this.getChildControl("board").add(widget, entry.layoutProperties);
        return widget;
      }
    },

    _onDragStart: function() {
      var spec = {
        duration: 400,
        timing: "ease-in-out",
        keep: 100,
        keyFrames : {
          0: {
            scale : [ "1", "1" ]
          },
          50: {
            scale : [ "1.2", "1.2" ]
          },
          100: {
            scale : [ "1", "1" ]
          }
        }
      };
      qx.bom.element.Animation.animate(this.__toolbarButtons['delete'].getContentElement().getDomElement(), spec);
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
          if (widget instanceof qx.ui.core.Spacer) {
            if (widget.getLayoutProperties().row === 0) {
              // do not save the first spacer row
              return;
            }
            settings.push({
              widget           : "qx.ui.core.Spacer",
              layoutProperties : widget.getLayoutProperties()
            })
          } else {
            var packageName = gosa.util.Reflection.getPackageName(widget);
            var sourceKey = packageName+".source";
            settings.push({
              widget           : packageName,
              source           : qx.core.Environment.get(sourceKey),
              layoutProperties : widget.getLayoutProperties(),
              settings         : widget.getConfiguration()
            })
          }
        }, this);
        gosa.io.Rpc.getInstance().cA("saveUserPreferences", "dashboard", settings)
        .then(function() {
          this.__toolbarButtons['save'].setEnabled(false);
          this.__settings = settings;
        }, this)
        .catch(function(error) {
          new gosa.ui.dialogs.Error(error.message).open();
        });
      }
    },

    /**
     * Handle pluginUpdate events from backend, reload the dashboard widget information
     */
    _onPluginUpdate: function() {
      // delete all upload widgets buttons (they have 'namespace' userData)
      this._createMenu.getChildren().forEach(function(button) {
        if (button.getUserData("namespace")) {
          button.destroy();
        }
      }, this);

      // add the uploaded widgets which can be downloaded from the backend
      gosa.io.Rpc.getInstance().cA("getDashboardWidgets")
      .then(function(widgets) {
        widgets.forEach(function(widget) {
          var displayName = widget.info.name;
          var button = new qx.ui.menu.Button(displayName);
          button.setUserData("namespace", widget.provides.namespace);
          this._createMenu.add(button);
          button.addListener("execute", this._loadFromBackend, this);
        }, this);
      }, this);

    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this.__gridLayout = null;
    Object.getOwnPropertyNames(this.__toolbarButtons).forEach(function(name) {
      this.__toolbarButtons[name].dispose();
    }, this);
    this.__toolbarButtons = null;
    gosa.io.Sse.getInstance().removeListener("pluginUpdate", this._onPluginUpdate, this);
    this._disposeObjects("_createMenu");
  },

  defer: function(statics) {
    // load available plugin-parts
    var parts = qx.io.PartLoader.getInstance().getParts();
    Object.getOwnPropertyNames(parts).forEach(function(partName) {
      if (partName.startsWith("gosa.plugins.")) {
        statics.registerPart(parts[partName]);
      }
    }, this);
  }
});
