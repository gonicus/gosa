/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.ui.form.renderer.LabelAbove", {
  extend: gosa.ui.form.renderer.Single,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function(form, show_dots) {
    this.base(arguments, form, show_dots);
    var layout = new qx.ui.layout.VBox(6);
    this._setLayout(layout);
  },

  members: {
    /**
     * Add a group of form items with the corresponding names. The names are
     * displayed as label.
     * The title is optional and is used as grouping for the given form
     * items.
     *
     * @param items {qx.ui.core.Widget[]} An array of form items to render.
     * @param names {String[]} An array of names for the form items.
     * @param title {String?} A title of the group you are adding.
     */
    addItems : function(items, names, title) {
      // add the header
      if (title != null) {
        this._add(this._createHeader(title));
      }

      // add the items
      for (var i = 0; i < items.length; i++) {
        var label = this._createLabel(names[i], items[i]);
        this._add(label);
        var item = items[i];
        label.setBuddy(item);
        this._add(item);

        this._connectVisibility(item, label);

        // store the names for translation
        if (qx.core.Environment.get("qx.dynlocale")) {
          this._names.push({name: names[i], label: label, item: items[i]});
        }
      }
    }
  }
});
