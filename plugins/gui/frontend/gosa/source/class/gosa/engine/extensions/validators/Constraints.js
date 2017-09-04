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


qx.Class.define("gosa.engine.extensions.validators.Constraints", {
  extend: qx.core.Object,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.base(arguments);

    this.__widgetCache = {};
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    constraints: {
      check: "Object"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __widgetCache: null,

    __getWidget: function(id, widgets) {
      if (!this.__widgetCache[id]) {
        widgets.some(function(widget) {
          if (widget.getAttribute() === id || widget.getWidgetName() === id) {
            this.__widgetCache[id] = widget;
            return true;
          }
        }, this);
      }
      return this.__widgetCache[id];
    },

    validate: function(widgets, manager) {
      var constraints = this.getConstraints();
      if (qx.lang.Object.isEmpty(constraints)) {
        // no constraints -> valid
        return true;
      }
      var valid = true;

      // reset all widgets
      widgets.forEach(function(w) {
        w.setValid(true);
      });

      Object.getOwnPropertyNames(constraints).forEach(function(name) {
        var widget = this.__getWidget(name, widgets);
        if (!widget) {
          this.error("no widget found for constraint option "+name);
        } else {
          // check if there is a constraint for the current selection
          var selection = gosa.ui.widgets.Widget.getSingleValue(widget.getValue());
          if (selection !== null && constraints[name].hasOwnProperty(selection)) {
            // check constraints
            constraints[name][selection].forEach(function(constraint) {
              // get related option
              var option = this.__getWidget(constraint.option, widgets);
              if (!option) {
                this.error("no widget found for related constraint option " + name);
              } else {
                var relatedSelection = gosa.ui.widgets.Widget.getSingleValue(option.getValue());
                if (relatedSelection === constraint.choice) {
                  widget.setInvalidMessage(qx.locale.Manager.tr("Value conflicts with '%1' option value '%2'", constraint.optionTitle, constraint.choiceTitle));
                  widget.setValid(false);
                  valid = false;
                }
              }
            }, this);
          }
        }
      }, this);
      return valid;
    }
  }
});