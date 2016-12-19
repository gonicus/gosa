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

    this.addListenerOnce("appear", this.draw, this);
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    __registry: {},

    registerWidget: function(name, widgetClass, options) {
      qx.core.Assert.assertString(name);
      qx.core.Assert.assertTrue(qx.Interface.classImplements(widgetClass, gosa.plugins.IPlugin),
      widgetClass+" does not implement the gosa.plugins.IPlugin interface");
      this.__registry[name] = {
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

    draw: function() {
      var row=0;
      var col=0;
      for (var i=0; i<this.getColumns(); i++) {
        this.__layout.setColumnFlex(i, 1);
      }

      // load dashboard settings from backend
      gosa.io.Rpc.getInstance().cA("loadUserPreferences", "dashboard")
      .then(function(result) {
        if (result) {
          this.__settings = result;
          var maxColumns = this.getColumns();
          var registry = gosa.view.Dashboard.getWidgetRegistry();
          this.__settings.forEach(function(entry) {
            var widgetName = entry.widget.toLowerCase();
            if (!registry[widgetName]) {
              this.warn("%s dashboard widget not registered", entry.widget);
            }
            else {
              var widget = new registry[widgetName].clazz();
              if (entry.settings) {
                widget.configure(entry.settings);
              }
              var options = registry[widgetName].options;
              if (options && options['theme']) {
                for (var key in options['theme']) {
                  if (key === "meta") {
                    qx.Theme.patch(gosa.theme.Theme, options['theme'][key]);
                  }
                  else {
                    qx.Theme.patch(gosa.theme[qx.lang.String.firstUp(key)], options['theme'][key]);
                  }
                }

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
      if(gosa.Session.getInstance().getUser()){
        gosa.io.Rpc.getInstance().cA("saveUserPreferences", "dashboard", this.__settings)
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
    this.save();
    this.__layout = null;
  }
});
