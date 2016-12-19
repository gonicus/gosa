/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2016 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Base class for all dashboard widgets
*/
qx.Class.define("gosa.plugins.AbstractDashboardWidget", {
  extend : qx.ui.core.Widget,
  implement: gosa.plugins.IPlugin,
  type: "abstract",
    
  properties : {
    appearance: {
      refine: true,
      init: "gosa-dashboard-widget"
    }
  },
    
  members : {
    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "title":
          control = new qx.ui.basic.Label();
          this._add(control);
          break;

        case "content":
          control = new qx.ui.container.Composite(new qx.ui.layout.Grow());
          this._add(control);
          break;
      }

      return control || this.base(arguments, id);
    },

    // property apply
    _applyTitle: function(value) {
      var control = this.getChildControl("title");
      if (value) {
        control.setValue(value);
        control.show();
      } else {
        control.exclude();
      }
    },

    // can be overridden by subclasses for more sophisticated configurations
    configure: function(properties) {
      this.set(properties);
    },

    /**
     * Return the user defined properties as Map
     * @return {Map}
     */
    getConfiguration: function() {
      var config = {};
      Object.getOwnPropertyNames(this).forEach(function(prop) {
        if (prop.substring(0, 7) === "$$user_") {
          var name = prop.substring(7);
          // user defined property value found, check if it is != its init value
          if (qx.util.PropertyUtil.getInitValue(this, name) !== this[prop]) {
            config[name] = this[prop];
          }
        }
      }, this);
      return config;
    }
  }
});