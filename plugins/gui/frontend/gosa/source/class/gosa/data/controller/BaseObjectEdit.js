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
 * Controller for the {@link gosa.ui.widget.ObjectEdit} widget; connects it to the model.
 */
qx.Class.define("gosa.data.controller.BaseObjectEdit", {
  extend : qx.core.Object,
  type: "abstract",

  properties : {
    modified : {
      check : "Boolean",
      init : false,
      event : "changeModified",
      apply: "_applyModified"
    },

    valid : {
      check : "Boolean",
      init : true,
      event : "changeValid"
    }
  },

  members : {
   _widget: null,

    _applyModified: function(value) {
      console.trace(value);
    },

    /**
     * @param attributeName {String}
     * @return {qx.ui.core.Widget | null} Existing attribute for the attribute name
     */
    getWidgetByAttributeName : function(attributeName) {
      qx.core.Assert.assertString(attributeName);
      var contexts = this._widget.getContexts();
      var map;

      for (var i=0; i < contexts.length; i++) {
        map = contexts[i].getWidgetRegistry().getMap();
        if (map.hasOwnProperty(attributeName)) {
          return map[attributeName];
        }
      }
      return null;
    },

    /**
     * @param attributeName {String}
     * @return {gosa.ui.widgets.QLabelWidget | null}
     */
    getBuddyByAttributeName : function(attributeName) {
      qx.core.Assert.assertString(attributeName);
      var contexts = this._widget.getContexts();
      var map;

      for (var i=0; i < contexts.length; i++) {
        map = contexts[i].getBuddyRegistry().getMap();
        if (map[attributeName]) {
          return map[attributeName];
        }
      }
      return null;
    },

    getActiveExtensions : function() {
      return {};
    }
  },

  destruct : function() {
    this._widget = null;
  }
});
