qx.Class.define("gosa.ui.base.Buttons", {

  type: "static",

  statics: {

    getButton : function(text, icon, tooltip) {
      var btn;
      if (icon) {
        btn = new qx.ui.form.Button(text, gosa.Config.getImagePath(icon, 22));
      } else {
        btn = new qx.ui.form.Button(text);
      }
      btn.addState("default");

      if (tooltip) {
        var tt = new qx.ui.tooltip.ToolTip(tooltip);
        btn.setToolTip(tt);
      }

      return btn;
    },

    getOkButton : function() {
      return gosa.ui.base.Buttons.getButton(qx.locale.Manager.tr("OK"), "actions/dialog-ok.png");
    },

    getCancelButton : function() {
      return gosa.ui.base.Buttons.getButton(qx.locale.Manager.tr("Cancel"), "actions/dialog-cancel.png");
    }
  }
});
