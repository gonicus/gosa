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

qx.Class.define("gosa.ui.form.renderer.Single", {
  extend: qx.ui.form.renderer.Single,

  construct : function(form, show_dots)
  {
    if (show_dots === false) {
      this.setShowDots(false);
    }
    this.base(arguments, form);
  },

  properties : {

    showDots: {
      check: "Boolean",
      init: true
    },

    controller: {
      check: "qx.data.controller.Form",
      nullable: true
    },

    headerAlign: {
      check: ["left", "center", "right"],
      init: "left"
    }
  },

  members: {

    getForm: function() {
      return this._form;
    },

    getLayout: function() {
      return this._getLayout();
    },

    /**
     * Creates the label text for the given form item.
     *
     * @param name {String} The content of the label without the
     *   trailing * and :
     * @param item {qx.ui.form.IForm} The item, which has the required state.
     * @return {String} The text for the given item.
     */
    _createLabelText : function(name, item)
    {
      var required = "";
      if (item.getRequired() && this.getShowDots()) {
       required = " <span style='color:red'>*</span> ";
      }

      // Create the label.
      return name + required;
    },
    /**
     * Creates a header label for the form groups.
     *
     * @param title {String} Creates a header label.
     * @return {qx.ui.basic.Label} The header for the form groups.
     */
    _createHeader : function(title) {
      var header = new qx.ui.basic.Label(title);
      // store labels for disposal
      this._labels.push(header);
      header.setFont("bold");
      if (this._row !== 0) {
        header.setMarginTop(10);
      }
      header.setAlignX(this.getHeaderAlign());
      return header;
    }
  }
});
