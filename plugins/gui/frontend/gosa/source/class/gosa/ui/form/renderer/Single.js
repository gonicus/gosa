/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

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
    }

  },

  members: {

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
    }

  }
});
