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
 * Creates a new dialog out of a dialog template.
 */
qx.Class.define("gosa.ui.dialogs.TemplateDialog",
{
  extend : gosa.ui.dialogs.Dialog,

  include : [gosa.ui.dialogs.MController],

  /**
   * @param template {String} The unparsed dialog template
   * @param controller {gosa.data.controller.ObjectEdit}
   * @param extension {String}
   */
  construct : function(template, controller, extension, valueIndex) {
    qx.core.Assert.assertObject(template);
    qx.core.Assert.assertInterface(controller, gosa.data.controller.ITemplateDialogCreator);
    qx.core.Assert.assertString(extension);

    this._parsedTemplate = template;
    this.setController(controller);
    this._extension = extension;
    this._valueIndex = valueIndex;

    this.base(arguments, this._getTemplateProperty("windowTitle"));
    this.setAutoDispose(true);

    this._addWidgets();
    this._addButtons();

    this.addListener("close", this._onClose, this);

    // necessary because contents are loaded on appear and it can only be centered with contents added
    this.addListenerOnce("resize", function() {
      this.center();
      (new qx.util.DeferredCall(this.center, this)).schedule();
    }, this);
  },

  /*
  *****************************************************************************
     EVENTS
  *****************************************************************************
  */
  events : {
    "send": "qx.event.type.Event"
  },

  members : {
    _parsedTemplate : null,
    _extension : null,
    _context: null,
    /**
     * If this dialog edits a certain value of a multivalue attribute this is the index of the value
     */
    _valueIndex: null,

    getContext: function() {
      return this._context;
    },

    _getTemplateProperty: function(name, type) {
      var t = this._parsedTemplate;
      if (t &&
          t.properties && typeof t.properties === "object" &&
          t.properties[name] && typeof t.properties[name] === type || "string") {
        return t.properties[name];
      }
      qx.core.Assert.fail("Cannot find valid "+name+" in dialog template");
    },

    _addButtons : function() {
      var ok = gosa.ui.base.Buttons.getOkButton();
      ok.addListener("execute", this._onOk, this);
      this.addButton(ok);
      this._context.bind("valid", ok, "enabled");

      if (this._getTemplateProperty("cancelable", "boolean") === true) {
        var cancel = gosa.ui.base.Buttons.getCancelButton();
        cancel.addListener("execute", this.close, this);
        this.addButton(cancel);
      }
    },

    _onOk: function(ev) {
      this.fireEvent("send");
      this.close();
    },

    _addWidgets : function() {
      var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      this.addElement(container, {flex : 1});

      this._context = new gosa.engine.Context(this._parsedTemplate, container, this._extension, this.getController(), this._valueIndex);
      this.getController().handleTemporaryContext && this.getController().handleTemporaryContext(this._context);
    },

    _onClose: function() {
      this.getController().cleanupContext && this.getController().cleanupContext(this._context);
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this._disposeObjects("_context");
  }
});
