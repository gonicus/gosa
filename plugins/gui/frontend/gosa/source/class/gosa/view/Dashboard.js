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
    this.__layout = new qx.ui.layout.Grid(5, 5);
    this._setLayout(this.__layout);
    this.__patchedThemes = {};

    this.addListenerOnce("appear", this.draw, this);
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

    draw: function() {
      var row=0;
      var col=0;
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
              this._add(widget, entry.layoutProperties);
              col++;
              if (col >= maxColumns) {
                col = 0;
                row++;
              }
            }
          }, this);
        }
      }, this);
    },

    /**
     * Save the current dashboard settings to the backend
     */
    save: function() {
      // Save settings back to the user model
      if(gosa.Session.getInstance().getUser()) {
        // collect information
        var settings = [];
        this.getChildren().forEach(function(widget) {
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
  }
});
