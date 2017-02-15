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

qx.Class.define("gosa.ui.widgets.QPushButtonWidget", {

  extend : gosa.ui.widgets.Widget,

  construct : function() {
    this.base(arguments);

    this.contents.setLayout(new qx.ui.layout.Canvas());
    this._widget = new qx.ui.form.Button();
    this._widget.addListener("execute", function() {
        if (this._dialog) {
          var d = this.getParent()._dialogs[this._dialog];
          if (d) {
            d.open();
          } else {
            this.error("no such dialog named '" + this._dialog + "'!");
          }
        }
      }, this);

    this.contents.add(this._widget, {
      top : 0,
      bottom : 0,
      left : 0,
      right : 0
    });
  },

  properties: {
    /**
     * The button label.
     */
    text : {
      init : "",
      check : "String",
      apply : "_setText",
      nullable: true
    },

    /**
     * Base name of a dialog class. On click on the button, this class is searched for in the namespace of
     * "gosa.ui.dialogs" and then a new such dialog will be created. Example: "ChangePasswordDialog" opens a new
     * "gosa.ui.dialogs.ChangePasswordDialog" dialog.
     */
    dialog : {
      init : null,
      nullable : true,
      check : "String",
      apply : "_applyDialog"
    }
  },

  members : {

    _widget : null,
    _dialog : null,
    _dialogExecutionListener : null,

    _setText : function(value) {
      this._widget.setLabel(this['tr'](value));
    },

    _applyGuiProperties : function(props) {
      // properties are null when widget gets destroyed
      if (!props) {
        return;
      }

      if (props.dialog && props.dialog.string) {
        this._dialog = props.dialog.string;
      }
      if (props.text && props.text.string) {
        this._setText(props.text.string);
      }
    },

    _applyDialog : function(value) {
      if (value) {
        this._createDialogExecutionListener();
      }
      else {
        this._removeDialogExecutionListener();
      }
    },

    _createDialogExecutionListener : function() {
      if (!this._dialogExecutionListener) {
        this._dialogExecutionListener = this._widget.addListener("execute", function() {
          var dialog = gosa.engine.WidgetFactory.createDialog(this.getDialog(), this._getController(), this.getExtension());
          dialog.open();
        }, this);
      }
    },

    _removeDialogExecutionListener : function() {
      if (this._dialogExecutionListener) {
        this._widget.removeListenerById(this._dialogExecutionListener);
        this._dialogExecutionListener = null;
      }
    }
  },

  destruct : function() {
    this._removeDialogExecutionListener();
  }
});
