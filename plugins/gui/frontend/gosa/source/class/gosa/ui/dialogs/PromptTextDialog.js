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
 * Ask the user to enter some text in a textfield.
 */
qx.Class.define("gosa.ui.dialogs.PromptTextDialog",
{
  extend : gosa.ui.dialogs.Dialog,

  construct : function(caption, icon, fieldName)
  {
    this.base(arguments, caption, icon);
    this.__initForm(fieldName);
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "ok": "qx.event.type.Data"
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members: {

    // overridden
    _createChildControlImpl: function(id) {
      var control;

      switch(id) {

        case "form":
          control = new qx.ui.form.Form();
          break;

        case "text":
          control = new qx.ui.form.TextField();
          control.set({
            required: true,
            width: 200
          });
          break;

        case "ok-button":
          control = gosa.ui.base.Buttons.getButton(this.tr("Ok"));
          control.addListener("execute", this._onOk, this);
          this.addButton(control);
          break;

        case "cancel-button":
          control = gosa.ui.base.Buttons.getButton(this.tr("Cancel"));
          control.addListener("execute", this.close, this);
          this.addButton(control);
          break;
      }

      return control || this.base(arguments, id);
    },

    __initForm: function(fieldName) {
      // Show Subject/Message pane
      var form = this.getChildControl("form");
      var text = this.getChildControl("text");

      form.add(text, fieldName, null, "text");

      this.addElement(new gosa.ui.form.renderer.Single(form, false));

      this._createChildControl("cancel-button");
      this._createChildControl("ok-button");
    },

    _onOk: function() {
      this.fireDataEvent("ok", this.getChildControl("text").getValue());
      this.close();
    }
  }
});

