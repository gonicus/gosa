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

qx.Class.define("gosa.ui.base.Buttons", {

  type: "static",

  statics: {

    getButton : function(text, icon, tooltip) {
      var btn;
      if (icon) {
        if (icon.startsWith("@")) {
          btn = new qx.ui.form.Button(text, icon);
          btn.getChildControl("icon").set({
            height: 22,
            width: 22,
            scale: true
          })
        } else {
          btn = new qx.ui.form.Button(text, gosa.Config.getImagePath(icon, 22));
        }
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
      return gosa.ui.base.Buttons.getButton(qx.locale.Manager.tr("OK"), "@Ligature/check");
    },

    getCancelButton : function() {
      return gosa.ui.base.Buttons.getButton(qx.locale.Manager.tr("Cancel"), "@Ligature/ban");
    }
  }
});
