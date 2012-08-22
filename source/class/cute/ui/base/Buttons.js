qx.Class.define("cute.ui.base.Buttons", {

  type: "static",

  statics: {

    getButton : function(text, icon, tooltip) {
      var btn = new qx.ui.form.Button(text, cute.Config.getImagePath(icon, 22));
      btn.addState("default");

      if (tooltip) {
        var tt = new qx.ui.tooltip.ToolTip(tooltip);
        btn.setToolTip(tt);
      }

      return btn;
    },

    getOkButton : function() {
      return cute.ui.base.Buttons.getButton(qx.locale.Manager.tr("OK"), "actions/dialog-ok.png");
    },

    getCancelButton : function() {
      return cute.ui.base.Buttons.getButton(qx.locale.Manager.tr("Cancel"), "actions/dialog-cancel.png");
    }
  }
});
