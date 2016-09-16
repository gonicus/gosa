/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Creates a new dialog out of a dialog template.
 */
qx.Class.define("gosa.ui.dialogs.TemplateDialog",
{
  extend : gosa.ui.dialogs.Dialog,

  include : [gosa.ui.dialogs.MController],

  /**
   * @param template {String} The unparsed dialog template
   */
  construct : function(template) {
    qx.core.Assert.assertString(template);
    this._parsedTemplate = gosa.util.Template.compileTemplate(template);

    this.base(arguments, this._getWindowTitle());
    this.setAutoDispose(true);

    this._addWidgets();
    this._addButtons();
  },

  members : {
    _parsedTemplate : null,

    _getWindowTitle : function() {
      var t = this._parsedTemplate;
      if (t &&
          t.properties && typeof t.properties === "object" &&
          t.properties.windowTitle && typeof t.properties.windowTitle === "string") {
            var windowTitle = t.properties.windowTitle;
            delete t.properties.windowTitle;
            delete t.properties.dialogName;
            return windowTitle;
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
      new gosa.engine.Context(this._parsedTemplate, container);
    }
  }
});
