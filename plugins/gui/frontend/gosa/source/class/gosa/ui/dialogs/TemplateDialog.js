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
  construct : function(template, controller, extension) {
    qx.core.Assert.assertObject(template);
    qx.core.Assert.assertInstance(controller, gosa.data.controller.ObjectEdit);
    qx.core.Assert.assertString(extension);

    this._parsedTemplate = template;
    this.setController(controller);
    this._extension = extension;

    this.base(arguments, this._getWindowTitle());
    this.setAutoDispose(true);

    this._addWidgets();
    this._addButtons();

    // necessary because contents are loaded on appear and it can only be centered with contents added
    this.addListenerOnce("resize", function() {
      this.center();
      (new qx.util.DeferredCall(this.center, this)).schedule();
    }, this);
  },

  members : {
    _parsedTemplate : null,
    _extension : null,
    _context: null,

    getContext: function() {
      return this._context;
    },

    _getWindowTitle : function() {
      var t = this._parsedTemplate;
      if (t &&
          t.properties && typeof t.properties === "object" &&
          t.properties.windowTitle && typeof t.properties.windowTitle === "string") {
            return t.properties.windowTitle;
          }
      qx.core.Assert.fail("Cannot find valid window title in dialog template");
    },

    _addButtons : function() {
      var ok = gosa.ui.base.Buttons.getOkButton();
      ok.addListener("execute", this.close, this);
      this.addButton(ok);
    },

    _addWidgets : function() {
      var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      this.addElement(container, {flex : 1});

      this._context = new gosa.engine.Context(this._parsedTemplate, container, this._extension, this.getController());
      this.getController().handleTemporaryContext(this._context);
    }
  }
});
