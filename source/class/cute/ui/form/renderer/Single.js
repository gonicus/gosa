qx.Class.define("cute.ui.form.renderer.Single", {
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
